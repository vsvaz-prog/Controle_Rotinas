CONTROLE DE ROTINAS - PCP
==========================

Como rodar:
1. Precisa ter Python e Flask instalados:
   pip install flask

2. Rode o arquivo:
   python app.py

3. Abra no navegador:
   http://localhost:5000
   (para acessar de outro dispositivo na mesma rede, use o IP do seu computador em vez de "localhost")

O que foi adicionado em cima do seu código original:
- Dashboard com total, concluídas, pendentes e % concluído (com barrinha de progresso)
- Campo de setor (hoje só "PCP", mas é só adicionar mais nomes na lista SETORES no topo do app.py)
- Prioridade (Baixa, Média, Alta) com cores
- Data/hora de criação automática
- Prazo (data), com aviso de "Atrasada" em vermelho quando passa do prazo e ainda está pendente
- Editar rotina (nome, setor, prioridade, prazo)
- Excluir rotina (com confirmação)
- Marcar como concluída / reabrir
- Layout novo (cards, cores, ícones, responsivo pra celular)

O banco (rotinas.db) é criado automaticamente na primeira vez que você roda o app,
na mesma pasta do app.py.
