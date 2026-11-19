# =============================================================================
# Lambda 2: entradaEstoque  (usada pelo COLABORADOR)
# Nome da função na AWS: entradaEstoque  |  Runtime: Python 3.12  |  Role: LabRole
# Arquivo no console: lambda_function.py   (handler: lambda_function.lambda_handler)
# Tempo limite recomendado: 10 s (envia um e-mail por cliente em espera)
#
# Recebe (JSON): {"titulo": "...", "quantidade": 2}
#  - Soma a quantidade ao estoque (cria o livro se não existir).
#  - Envia e-mail "seu livro chegou" a todos em "interessados" e esvazia a lista.
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
    titulo = dados.get('titulo', '').strip().lower()
    try:
        quantidade = int(dados.get('quantidade', 0))
    except ValueError:
        quantidade = 0

    if not titulo or quantidade <= 0:
        return resposta(400, 'Informe o título e uma quantidade maior que zero.')

    # Soma ao estoque e devolve o item atualizado
    item = tabela.update_item(
        Key={'titulo': titulo},
        UpdateExpression='SET quantidade = if_not_exists(quantidade, :zero) + :q, '
                         'vendidos = if_not_exists(vendidos, :zero)',
        ExpressionAttributeValues={':q': quantidade, ':zero': 0},
        ReturnValues='ALL_NEW',
    )['Attributes']

    interessados = item.get('interessados', [])

    for email in interessados:
        enviar_email(email, 'Sebo - seu livro chegou',
                     f'O livro "{titulo}" que você queria chegou! '
                     'Compareça à livraria para efetivar a compra.')

    if interessados:
        tabela.update_item(
            Key={'titulo': titulo},
            UpdateExpression='SET interessados = :vazia',
            ExpressionAttributeValues={':vazia': []},
        )

    return resposta(200, f'Estoque atualizado: {item["quantidade"]} unidade(s). '
                         f'{len(interessados)} cliente(s) avisado(s).')
