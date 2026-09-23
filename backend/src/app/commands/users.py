import argparse
import getpass
import uuid

from pydantic import TypeAdapter, ValidationError
from sqlalchemy import delete, select

from app.api.schemas.common import Name
from app.core.security import hasher
from app.db.models import AuditEvent, LoginSession, User
from app.db.session import SessionFactory


def main():
    parser = argparse.ArgumentParser(description="Provisionar uma conta local IF-Arbitra")
    parser.add_argument("login")
    parser.add_argument("name", nargs="?")
    parser.add_argument("--admin", action="store_true")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Redefinir senha após verificar a identidade por canal institucional",
    )
    args = parser.parse_args()
    try:
        args.login = TypeAdapter(Name).validate_python(args.login.strip().casefold())
        if args.name is not None:
            args.name = TypeAdapter(Name).validate_python(args.name.strip())
    except ValidationError:
        parser.error("Nome e identificador devem ter entre 2 e 160 caracteres")
    password = getpass.getpass("Senha (mínimo 12 caracteres): ")
    if len(password) < 12 or len(password) > 256:
        parser.error("Senha deve ter entre 12 e 256 caracteres")
    if password != getpass.getpass("Confirme a senha: "):
        parser.error("Senhas diferentes")
    with SessionFactory.begin() as db:
        user = db.scalar(select(User).where(User.login == args.login.casefold()).with_for_update())
        if args.reset_password:
            if not user or args.admin:
                parser.error("Informe uma conta existente; redefinição não altera permissões")
            user.password_hash = hasher.hash(password)
            db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
        else:
            if user or not args.name:
                parser.error("Informe um identificador novo e o nome completo")
            user = User(
                login=args.login.casefold(),
                name=args.name,
                role="ADMIN" if args.admin else "STUDENT",
                password_hash=hasher.hash(password),
            )
            db.add(user)
        db.flush()
        db.add(
            AuditEvent(
                event_type="ADMIN_ACTION",
                entity_type="USER",
                entity_id=str(user.id),
                request_id=str(uuid.uuid4()),
                payload={
                    "action": "PASSWORD_RESET" if args.reset_password else "ACCOUNT_PROVISIONED",
                    "source": "operator_cli",
                    "role": user.role,
                },
            )
        )
    print("Senha redefinida; sessões revogadas." if args.reset_password else "Conta criada.")


if __name__ == "__main__":
    main()
