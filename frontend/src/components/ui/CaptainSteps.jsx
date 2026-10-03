import { Check } from 'lucide-react';

const steps = ['Montar grupo', 'Enviar preferências', 'Aguardar resultado'];

export default function CaptainSteps({ current, groupConfirmed = false, preferencesSent = false }) {
  return <ol className="app-steps app-captain-steps" aria-label="Seu cadastro em três etapas">
    {steps.map((label, index) => {
      const number = index + 1;
      const done = number === 1 ? groupConfirmed : number === 2 ? preferencesSent : false;
      return <li className={`app-step ${done ? 'done' : ''} ${number === current ? 'active' : ''}`} key={label} aria-current={number === current ? 'step' : undefined}>
        <span className="app-step-number">{done ? <Check size={16} aria-hidden="true"/> : number}</span>
        <strong>{label}</strong><small>{done ? 'Concluído' : number === current ? 'Você está aqui' : 'Próximo passo'}</small>
      </li>;
    })}
  </ol>;
}
