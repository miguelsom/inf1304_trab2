# =============================================================================
# Lambda 1: solicitarLivro  (usada pelo CLIENTE)
# Nome da função na AWS: solicitarLivro  |  Runtime: Python 3.12  |  Role: LabRole
# Arquivo no console: lambda_function.py   (handler: lambda_function.lambda_handler)
#
# Recebe (JSON): {"email": "...", "titulo": "..."}
#  - Livro com estoque  -> envia e-mail "compareça à livraria".
#  - Sem estoque/novo   -> grava o e-mail em "interessados" e envia e-mail
#                          "indisponível, avisaremos quando chegar".
# =============================================================================

import json
import base64
import boto3

# -----------------------------------------------------------------------------
# >>> AJUSTAR AO TROCAR DE CONTA <<<
# TOPICO_ARN: copie o ARN do SEU tópico em SNS -> Tópicos -> sebo -> Detalhes.
# Formato: arn:aws:sns:us-east-1:<ID_DA_SUA_CONTA_12_DIGITOS>:sebo
# Valor abaixo = conta da entrega (ID 654654484494).
# -----------------------------------------------------------------------------
TOPICO_ARN = 'arn:aws:sns:us-east-1:654654484494:sebo'

# Só altere se criar a tabela com outro nome (padrão: Livros)
TABELA = 'Livros'

tabela = boto3.resource('dynamodb').Table(TABELA)
sns = boto3.client('sns')


def ler_corpo(event):
    """Lê o JSON enviado pela página (Function URL pode mandar em base64)."""
    corpo = event.get('body') or '{}'
    if event.get('isBase64Encoded'):
        corpo = base64.b64decode(corpo).decode('utf-8')
    return json.loads(corpo)


def resposta(status, mensagem):
    return {'statusCode': status, 'body': json.dumps({'mensagem': mensagem})}


def enviar_email(email, assunto, mensagem):
    # O atributo "email" faz a política de filtro da assinatura no SNS
    # entregar a mensagem SOMENTE para este cliente.
    sns.publish(
        TopicArn=TOPICO_ARN,
        Subject=assunto,
        Message=mensagem,
        MessageAttributes={'email': {'DataType': 'String', 'StringValue': email}},
    )


def lambda_handler(event, context):
    dados = ler_corpo(event)
    email = dados.get('email', '').strip().lower()
    titulo = dados.get('titulo', '').strip().lower()

    if not email or not titulo:
        return resposta(400, 'Informe e-mail e título.')

    livro = tabela.get_item(Key={'titulo': titulo}).get('Item')

    # Livro disponível
    if livro and livro.get('quantidade', 0) > 0:
        enviar_email(email, 'Sebo - livro disponivel',
                     f'O livro "{titulo}" está disponível! '
                     'Compareça à livraria para efetivar a compra.')
        return resposta(200, 'Livro disponível! Enviamos um e-mail para você.')

    # Livro indisponível: registra interesse (sem duplicar o e-mail)
    if not livro or email not in livro.get('interessados', []):
        tabela.update_item(
            Key={'titulo': titulo},
            UpdateExpression='SET interessados = list_append(if_not_exists(interessados, :vazia), :email), '
                             'quantidade = if_not_exists(quantidade, :zero), '
                             'vendidos = if_not_exists(vendidos, :zero)',
            ExpressionAttributeValues={':vazia': [], ':email': [email], ':zero': 0},
        )

    enviar_email(email, 'Sebo - livro indisponivel',
                 f'O livro "{titulo}" não está disponível no momento. '
                 'Avisaremos por e-mail assim que ele chegar.')
    return resposta(200, 'Livro indisponível. Você será avisado por e-mail quando chegar.')
