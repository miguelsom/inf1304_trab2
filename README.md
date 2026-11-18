# Sebo na AWS

Segundo Trabalho de Distribuição e Concorrência (INF1304) — 2026/2

**Integrantes:** Miguel Soares de Oliveira Mendes, Simão Pedro Ferreira de Oliveira e
Luana Göbel Dall'Occhio.

## O que é

Aplicação para uma livraria no estilo sebo, feita inteiramente na AWS.

- O **cliente** informa o livro que quer. Se houver estoque, recebe um e-mail para ir à
  livraria. Se não houver, entra numa lista de espera e é avisado por e-mail quando o
  livro chegar.
- O **colaborador** registra a chegada de livros e as vendas, mantendo o estoque em dia.

A solução usa **3 funções Lambda, 1 tabela DynamoDB, 1 tópico SNS e 1 página HTML**.

```
Cliente / Colaborador
        │
   index.html ──HTTPS POST──► Lambda solicitarLivro ─┐
                         ├──► Lambda entradaEstoque ─┼──► DynamoDB "Livros"
                         └──► Lambda registrarVenda ─┘
              (solicitarLivro e entradaEstoque) ──► SNS "sebo" ──► e-mail do cliente
```

## Estrutura

```
├── README.md                       este arquivo
├── SETUP.md                        como montar o projeto na AWS, passo a passo
├── relatorio/
│   ├── Relatorio_Sebo_AWS.pdf      relatório do trabalho
│   └── Relatorio_Sebo_AWS.docx     mesmo relatório, editável
└── codigo/
    ├── lambda_solicitar_livro.py   Lambda solicitarLivro  (cliente pede um livro)
    ├── lambda_entrada_estoque.py   Lambda entradaEstoque  (chegada de livros)
    ├── lambda_registrar_venda.py   Lambda registrarVenda  (venda no balcão)
    ├── index.html                  interface web (abrir no navegador)
    └── filtro_assinatura_sns.json  modelo da política de filtro do SNS
```

Os diagramas (blocos, fluxo de dados e sequência) estão no relatório.

## Como usar

1. Ligar o AWS Academy Learner Lab da conta da entrega (**Start Lab**).
2. Abrir `codigo/index.html` no navegador.
3. Usar a **Área do cliente** ou a **Área do colaborador**.

Para montar o projeto do zero em outra conta, siga o [SETUP.md](SETUP.md).

## Conta do AWS Academy

A implementação avaliada está no Learner Lab de **Miguel Soares de Oliveira Mendes**
(usuário `voclabs/user5644255`, ID da conta `6546-5448-4494`), região `us-east-1`.
