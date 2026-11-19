# =============================================================================
# Lambda 3: registrarVenda  (usada pelo COLABORADOR)
# Nome da função na AWS: registrarVenda  |  Runtime: Python 3.12  |  Role: LabRole
# Arquivo no console: lambda_function.py   (handler: lambda_function.lambda_handler)
#
# Recebe (JSON): {"titulo": "..."}
#  - Tira 1 do estoque e soma 1 em "vendidos". Recusa se o estoque estiver zerado.
#
# Esta função NÃO usa o SNS: não há nada para ajustar ao trocar de conta
# (a menos que a tabela tenha outro nome).
# =============================================================================

import json
import base64
import boto3

# Só altere se criar a tabela com outro nome (padrão: Livros)
TABELA = 'Livros'

tabela = boto3.resource('dynamodb').Table(TABELA)


def ler_corpo(event):
    """Lê o JSON enviado pela página (Function URL pode mandar em base64)."""
    corpo = event.get('body') or '{}'
    if event.get('isBase64Encoded'):
        corpo = base64.b64decode(corpo).decode('utf-8')
    return json.loads(corpo)


def resposta(status, mensagem):
    return {'statusCode': status, 'body': json.dumps({'mensagem': mensagem})}


def lambda_handler(event, context):
    dados = ler_corpo(event)
    titulo = dados.get('titulo', '').strip().lower()

    if not titulo:
        return resposta(400, 'Informe o título.')

    try:
        item = tabela.update_item(
            Key={'titulo': titulo},
            UpdateExpression='SET quantidade = quantidade - :um, '
                             'vendidos = if_not_exists(vendidos, :zero) + :um',
            ConditionExpression='quantidade > :zero',   # só vende se houver estoque
            ExpressionAttributeValues={':um': 1, ':zero': 0},
            ReturnValues='ALL_NEW',
        )['Attributes']
    except tabela.meta.client.exceptions.ConditionalCheckFailedException:
        return resposta(400, 'Livro sem estoque ou não cadastrado.')

    return resposta(200, f'Venda registrada. Restam {item["quantidade"]} unidade(s).')
