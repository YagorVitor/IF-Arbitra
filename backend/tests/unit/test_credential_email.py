from app.services.credential_email import credential_message


def test_captain_email_contains_personalized_access_and_platform_in_both_formats():
    message = credential_message(
        name="Lucas A. S. Santos",
        email="a.severino@aluno.ifsp.edu.br",
        password="EXEMPLO8",
        frontend_url="https://if-arbitra-frontend.vercel.app/",
        sender="IF-Arbitra <noreply@example.org>",
    )
    assert message["To"] == "a.severino@aluno.ifsp.edu.br"
    assert message["Subject"].startswith("IF-Arbitra")
    for format_type in ("plain", "html"):
        body = message.get_body(preferencelist=(format_type,)).get_content()
        assert "Lucas A. S. Santos" in body
        assert "a.severino@aluno.ifsp.edu.br" in body
        assert "EXEMPLO8" in body
        assert "https://if-arbitra-frontend.vercel.app" in body
        assert "Instituto Federal de São Paulo" in body
        assert "exclusivo dos capitães" in body
    html = message.get_body(preferencelist=("html",)).get_content()
    assert 'href="https://if-arbitra-frontend.vercel.app"' in html


def test_html_escapes_personal_data_and_password_without_changing_plain_text():
    message = credential_message(
        name='<Lucas & "Santos">',
        email="lucas@example.org",
        password='A<&"B',
        frontend_url="https://example.org",
        sender="noreply@example.org",
    )
    html = message.get_body(preferencelist=("html",)).get_content()
    plain = message.get_body(preferencelist=("plain",)).get_content()
    assert "&lt;Lucas &amp; &quot;Santos&quot;&gt;" in html
    assert "A&lt;&amp;&quot;B" in html
    assert '<Lucas & "Santos">' in plain
    assert 'A<&"B' in plain
