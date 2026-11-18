# SETUP — Sebo na AWS

Guia para montar o projeto do zero numa conta do **AWS Academy Learner Lab**.
Os arquivos já estão configurados para a **conta da entrega**. Para usar outra conta,
siga a [seção 3](#3-trocar-de-conta--o-que-ajustar) e troque apenas os campos marcados com
`>>> AJUSTAR AO TROCAR DE CONTA <<<`.

---

## 1. Visão geral (o macro)

São **5 coisas** para configurar. Quatro ficam na AWS e uma é a página no seu computador:

| # | O quê | Serviço AWS | Nome a usar | Para que serve |
|---|---|---|---|---|
| 1 | Tabela | DynamoDB | `Livros` | Guarda cada livro: estoque (`quantidade`), total vendido (`vendidos`) e a lista de e-mails esperando o livro (`interessados`). |
| 2 | Tópico de e-mail | SNS (Standard) | `sebo` | Envia os e-mails. Cada cliente é inscrito com um **filtro** pelo próprio e-mail, para receber só as mensagens dele. |
| 3 | Função de pedido | Lambda | `solicitarLivro` | O cliente pede um livro. Com estoque, recebe "compareça à livraria". Sem estoque, entra na lista de espera e recebe "avisaremos". |
| 4 | Função de chegada | Lambda | `entradaEstoque` | O colaborador registra a chegada de livros. Soma ao estoque e avisa por e-mail todos que estavam esperando. |
| 5 | Função de venda | Lambda | `registrarVenda` | O colaborador registra uma venda. Tira 1 do estoque e soma 1 em vendidos, e recusa se não houver estoque. |
| — | Interface | (nenhum, arquivo local) | `index.html` | Página com área do cliente e área do colaborador. Chama as 3 Lambdas pelas *Function URLs*. |

Como as peças se ligam:

```
Cliente / Colaborador
        │
   index.html  ──HTTPS POST (Function URL)──►  Lambda solicitarLivro ─┐
                                          ├─►  Lambda entradaEstoque ─┼──► DynamoDB "Livros"
                                          └─►  Lambda registrarVenda ─┘
                                (solicitarLivro e entradaEstoque) ──publish──► SNS "sebo" ──► e-mail do cliente
```

Os diagramas completos estão no relatório (pasta `relatorio/`).

**Por que não há API Gateway?** Cada Lambda tem uma *Function URL*, que é um endereço HTTPS
próprio. A página chama essa URL diretamente. É mais simples e atende ao enunciado.

**Tempo total:** cerca de 20 minutos. **Região:** sempre `us-east-1` (Norte da Virgínia).

---

## 2. Passo a passo detalhado na AWS

> Os links do console só funcionam **depois** de abrir o console pelo Learner Lab (passo 2.0).
> Os nomes (`Livros`, `titulo`, `sebo`, nomes das funções) devem ser escritos **exatamente assim**,
> porque o código depende deles.

### 2.0 Abrir o Learner Lab

1. Entre em <https://awsacademy.instructure.com>, abra o curso e vá em
   **Modules → Launch AWS Academy Learner Lab**.
2. Clique em **Start Lab** e espere o indicador ao lado de "AWS" ficar **verde**.
   Amarelo significa que ainda está ligando.
3. Clique em **AWS**. O console abre numa nova aba.
4. Confira no canto superior direito:
   - o usuário deve aparecer como `voclabs/user...`. Se aparecer outro nome, você está numa
     conta pessoal: saia dela e entre de novo pelo Learner Lab;
   - a região deve ser **Norte da Virgínia (us-east-1)**.
5. **Anote o ID da conta (12 dígitos)**, que aparece no canto superior direito
   (por exemplo, `6546-5448-4494` → `654654484494`). Ele vai entrar no ARN do tópico.

> O lab desliga sozinho ao fim do tempo (cerca de 4 h), mas **os recursos continuam lá**.
> Para usar de novo, basta clicar em **Start Lab**.

### 2.1 Criar a tabela (DynamoDB)

1. Abra <https://us-east-1.console.aws.amazon.com/dynamodbv2/home?region=us-east-1#create-table>
2. Preencha:
   - **Nome da tabela:** `Livros`
   - **Chave de partição:** `titulo`, tipo **String**
   - Não adicione chave de classificação.
3. Deixe o resto no padrão e clique em **Criar tabela**.
4. Espere o status ficar **Ativo**.

Não é preciso criar as outras colunas: as Lambdas criam `quantidade`, `vendidos` e
`interessados` sozinhas na primeira gravação.

### 2.2 Criar o tópico de e-mail (SNS)

1. Abra <https://us-east-1.console.aws.amazon.com/sns/v3/home?region=us-east-1#/create-topic>
2. Em **Tipo**, marque **Padrão** (Standard).
   - ⚠️ **Não use FIFO.** Tópico FIFO não aceita e-mail: a opção "E-mail" nem aparece
     ao criar a assinatura.
3. **Nome:** `sebo`.
4. Clique em **Criar tópico**.
5. Na tela do tópico, em **Detalhes**, **copie o ARN**. Ele tem o formato:
   ```
   arn:aws:sns:us-east-1:<ID_DA_CONTA>:sebo
   ```
   Confira se termina em `:sebo`, **sem** `.fifo`.

### 2.3 Inscrever cada cliente no tópico (com filtro)

O enunciado considera que o cliente já está inscrito no tópico pela interface da AWS.
Faça isto **para cada e-mail** que vai receber mensagens. Para a demonstração, inscreva pelo
menos um e-mail. Com dois, dá para mostrar que cada um recebe só o que é dele.

1. No tópico `sebo`, clique em **Criar assinatura**.
2. Preencha:
   - **ARN do tópico:** o do `sebo` (já vem preenchido)
   - **Protocolo:** **E-mail**
   - **Endpoint:** o e-mail do cliente. Confira letra por letra, porque um erro aqui faz o
     e-mail de confirmação nunca chegar.
3. Abra **Política de filtro de assinatura** e ative.
4. **Escopo da política de filtro:** **Atributos da mensagem**.
5. Cole o JSON abaixo com **o mesmo e-mail, em minúsculas**. O modelo está em
   `codigo/filtro_assinatura_sns.json`:
   ```json
   {"email": ["cliente@exemplo.com"]}
   ```
6. Clique em **Criar assinatura**.
7. O cliente abre o e-mail **"AWS Notification - Subscription Confirmation"** e clica em
   **Confirm subscription**. Olhe também no spam.
8. Na lista de assinaturas, o status deve ficar **Confirmado**:
   <https://us-east-1.console.aws.amazon.com/sns/v3/home?region=us-east-1#/subscriptions>

**Para que serve o filtro?** Publicar num tópico manda a mensagem para *todos* os inscritos.
As Lambdas publicam com o atributo `email`, e o SNS entrega só à assinatura cujo filtro
corresponde. Sem o filtro, todo mundo receberia o e-mail de todo mundo.

> Uma assinatura que ficou como "Confirmação pendente" (por exemplo, com e-mail errado) não pode
> ser excluída manualmente. Ela some sozinha em cerca de 3 dias e não atrapalha nada.
> A assinatura `RedshiftSNS`, que já vem no Learner Lab, também deve ser ignorada; **não apague**.

### 2.4 Criar as 3 funções Lambda

Repita os passos abaixo **três vezes**:

| Nome da função | Arquivo de código (pasta `codigo/`) | Usa o SNS? | Tempo limite |
|---|---|---|---|
| `solicitarLivro` | `lambda_solicitar_livro.py` | Sim | padrão (3 s) |
| `entradaEstoque` | `lambda_entrada_estoque.py` | Sim | **10 s** |
| `registrarVenda` | `lambda_registrar_venda.py` | Não | padrão (3 s) |

#### a) Criar a função

1. Abra <https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/create/function>
2. Marque **Criar do zero** e preencha:
   - **Nome da função:** conforme a tabela acima
   - **Tempo de execução:** **Python 3.12**
3. Abra **▶ Configurações adicionais** e ajuste estas duas chaves (deixe todas as outras
   desligadas):
   - **Personalizar perfil de execução:** ative, marque *usar um perfil existente* e escolha
     **LabRole**.
     - ⚠️ Sem isso aparece o erro `not authorized to perform: iam:CreateRole`. O Learner Lab
       não deixa criar perfis IAM novos, então é obrigatório usar a `LabRole`, que já existe.
   - **URL da função:** ative e configure:
     - **Tipo de autenticação:** `NONE`
     - **CORS:** ative, com **Permitir origem** `*`, **Permitir cabeçalhos** `content-type`
       e **Permitir métodos** `POST`. No resumo deve aparecer "CORS: Sim".
4. Clique em **Criar função** (ou **Create Event Function**).

> Em versões mais antigas do console, a role fica em **"Alterar a função de execução padrão"**,
> e a URL é criada depois em **Configuração → URL da função → Criar URL de função**.
> As opções são as mesmas.

#### b) Colar o código

1. Na aba **Código**, abra o arquivo `lambda_function.py`.
2. Apague todo o conteúdo e cole o conteúdo do arquivo `.py` correspondente.
3. **Mantenha o nome do arquivo `lambda_function.py`.** Se renomear, a Lambda não encontra o
   código e dá o erro `Unable to import module 'lambda_function'`.
4. Em `solicitarLivro` e `entradaEstoque`, confira a linha `TOPICO_ARN`
   (veja a [seção 3](#3-trocar-de-conta--o-que-ajustar)).
5. Clique em **Deploy** e espere a mensagem "atualizada com êxito".

#### c) Tempo limite (só no `entradaEstoque`)

1. Vá em **Configuração → Configuração geral → Editar**.
2. Mude **Tempo limite** para **10 s** e salve.

Essa função envia um e-mail por cliente em espera e precisa de mais tempo que o padrão.

#### d) Copiar a URL da função

Na **Visão geral da função**, no lado direito, abaixo do ARN, fica o campo **URL da função**.
Copie esse link e anote de qual função ele é.

- O formato certo é `https://xxxxxxxx.lambda-url.us-east-1.on.aws/`.
- Não confunda com o **ARN** (`arn:aws:lambda:...`) nem com o endereço da página do console.

#### e) Teste rápido no console (opcional)

Na aba **Testar** do `solicitarLivro`, crie um evento com o conteúdo abaixo e clique em **Testar**:

```json
{"body": "{\"email\": \"cliente@exemplo.com\", \"titulo\": \"dom casmurro\"}"}
```

O resultado esperado é `statusCode` 200, o e-mail "Sebo - livro indisponivel" na caixa do
cliente e o item `dom casmurro` na tabela.

### 2.5 Configurar a interface (`index.html`)

1. Abra `codigo/index.html` num editor de texto (Bloco de Notas, VS Code etc.).
2. No começo do `<script>`, cole as 3 URLs nas constantes:
   ```js
   const URL_SOLICITAR = 'https://....lambda-url.us-east-1.on.aws/';  // solicitarLivro
   const URL_ENTRADA   = 'https://....lambda-url.us-east-1.on.aws/';  // entradaEstoque
   const URL_VENDA     = 'https://....lambda-url.us-east-1.on.aws/';  // registrarVenda
   ```
3. Salve e abra o arquivo com dois cliques. Ele roda direto no navegador, sem servidor.

### 2.6 Roteiro de teste

Deixe a tabela aberta numa aba para acompanhar as mudanças:
<https://us-east-1.console.aws.amazon.com/dynamodbv2/home?region=us-east-1#item-explorer?table=Livros>
Aperte F5 a cada passo.

| # | Onde | Ação | Resultado esperado |
|---|---|---|---|
| 1 | Cliente | E-mail inscrito + título novo (ex.: `O Cortiço`) → **Tenho interesse** | A página mostra "Livro indisponível...". Chega o e-mail "Sebo - livro indisponivel". Na tabela, o e-mail aparece em `interessados` e `quantidade` fica 0. |
| 2 | Colaborador | Mesmo título, quantidade `2` → **Registrar chegada** | A página mostra "2 unidade(s). 1 cliente(s) avisado(s)". Chega o e-mail "Sebo - seu livro chegou". Na tabela, `quantidade` fica 2 e `interessados` fica vazio. |
| 3 | Cliente | Mesmo e-mail e título → **Tenho interesse** | A página mostra "Livro disponível!". Chega o e-mail "Sebo - livro disponivel". |
| 4 | Colaborador | **Registrar venda** 3 vezes | A página mostra "Restam 1", depois "Restam 0", depois "Livro sem estoque". Na tabela, `vendidos` fica 2. |

---

## 3. Trocar de conta — o que ajustar

Para rodar em outra conta, refaça a seção 2 nessa conta e troque **só estes campos**.
Todos estão marcados no código com `>>> AJUSTAR AO TROCAR DE CONTA <<<`.

| # | Arquivo | Campo | Onde achar o novo valor |
|---|---|---|---|
| 1 | `codigo/lambda_solicitar_livro.py` | `TOPICO_ARN` | SNS → Tópicos → sebo → Detalhes → ARN |
| 2 | `codigo/lambda_entrada_estoque.py` | `TOPICO_ARN` | o mesmo ARN do item 1 |
| 3 | `codigo/index.html` | `URL_SOLICITAR` | Lambda → solicitarLivro → Visão geral → URL da função |
| 4 | `codigo/index.html` | `URL_ENTRADA` | Lambda → entradaEstoque → Visão geral → URL da função |
| 5 | `codigo/index.html` | `URL_VENDA` | Lambda → registrarVenda → Visão geral → URL da função |
| 6 | Console SNS (não é arquivo) | Assinaturas e filtros | Seção 2.3, com os e-mails que vão testar |

**O que NÃO muda:** o nome da tabela (`Livros`), a chave (`titulo`), o nome do tópico
(`sebo`), os nomes das funções, a região (`us-east-1`) e a role (`LabRole`), desde que
sejam usados os mesmos nomes da seção 2.

### 3.1 Ambientes já montados

O projeto está montado em duas contas, com a mesma configuração. Para usar uma delas,
copie as URLs correspondentes para o `index.html`.

| Campo | Ambiente 1 — **entrega oficial** (já no `index.html`) | Ambiente 2 — reserva |
|---|---|---|
| `URL_SOLICITAR` | `https://twv746thww6nlc5ar537npvnz40ntrsi.lambda-url.us-east-1.on.aws/` | `https://av2tqjtyq24ww5fgxrbzbmqyqa0uhdyb.lambda-url.us-east-1.on.aws/` |
| `URL_ENTRADA` | `https://pcyctdpq42ml7nwvdjmbzpoceq0gbilb.lambda-url.us-east-1.on.aws/` | `https://k4kmqnqjsywhviwta3abd537qm0tcouu.lambda-url.us-east-1.on.aws/` |
| `URL_VENDA` | `https://7d5izk2ym3p72o6adtztgc6lra0fejxn.lambda-url.us-east-1.on.aws/` | `https://kv5ijfniktiokuqdrafyusx5p40hghzp.lambda-url.us-east-1.on.aws/` |

O ambiente 1 é o Learner Lab de **Miguel Soares de Oliveira Mendes**
(`voclabs/user5644255`, ID da conta `6546-5448-4494`). Nele, o `TOPICO_ARN` é
`arn:aws:sns:us-east-1:654654484494:sebo`, que já está nas Lambdas.

> Cada ambiente só responde enquanto o Learner Lab da sua conta estiver ligado.

---

## 4. Problemas comuns

| Sintoma | Causa | Solução |
|---|---|---|
| A opção "E-mail" não aparece no Protocolo do SNS | Tópico criado como FIFO | Excluir o tópico e recriar como **Padrão** |
| O e-mail de confirmação da assinatura não chega | E-mail digitado errado, ou mensagem no spam | Conferir o Endpoint na assinatura e olhar o spam |
| `iam:CreateRole ... not authorized` ao criar a Lambda | O console tentou criar um perfil novo | Usar **LabRole** em *Personalizar perfil de execução* |
| `Unable to import module 'lambda_function'` | O arquivo foi renomeado | Voltar o nome para `lambda_function.py` |
| A página mostra "Erro de comunicação" | Lab desligado, URL errada, ou CORS desativado | Ligar o lab; conferir as URLs; ativar o CORS na URL da função. F12 → Console mostra o erro exato |
| A página mostra "Internal Server Error" | Erro dentro da Lambda | Lambda → **Monitor → Visualizar logs do CloudWatch** → log mais recente |
| `AccessDenied` no log | A função não está com a LabRole | Configuração → Permissões → trocar para LabRole |
| `ResourceNotFoundException` no log | Tabela com outro nome, região errada, ou ARN de outra conta | Conferir `Livros`, `us-east-1` e o `TOPICO_ARN` |
| A página funciona, mas o e-mail não chega | Assinatura não confirmada, ou filtro com e-mail diferente do digitado | Conferir o status **Confirmado** e o JSON do filtro (minúsculas) |

Logs de cada função:

- solicitarLivro: <https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252FsolicitarLivro>
- entradaEstoque: <https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252FentradaEstoque>
- registrarVenda: <https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252FregistrarVenda>
