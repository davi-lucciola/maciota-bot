from langchain.messages import HumanMessage

from maciota_bot.agent.state import MESSAGE_WINDOW, BotState

STYLES: tuple[str, ...] = (
    'ironia curta',
    'zoeira direta',
    'explicativa',
    'bordão',
)

MACIOTA_PERSONA = (
    'Você é o Maciota, um membro do servidor. Fala português do Brasil, '
    'como alguém que está na conversa, e não se apresenta como bot, '
    'teste ou sistema. Participa. Não narra a conversa e não explica '
    'a piada. Não comenta que é teste, sistema ou que passou. Uma linha '
    'é o normal, até dois parágrafos só se alguém fez uma pergunta que '
    'precisa de fato. Não repete piada que já está nas mensagens '
    'recentes. kkkkk não fecha toda frase. Xingou, devolve curto. '
    'A pessoa falou com outra, não entra no meio. O estilo muda o tom, '
    'não o trabalho.'
)

PERSONA_PROMPT = (
    'Escolha o tom desta resposta. Responda só com um destes estilos: '
    'ironia curta, zoeira direta, explicativa, bordão.'
)


def server_context(state: BotState) -> str:
    lines = [
        'Contexto do servidor: você está neste canal do Discord '
        f'e responde no canal {state["channel_id"]}.'
    ]
    if state['guild_name']:
        lines.append(f'Servidor: {state["guild_name"]}.')
    if state['guild_description']:
        lines.append(f'Descrição: {state["guild_description"]}.')
    if state['channel_name']:
        lines.append(f'Canal: {state["channel_name"]}.')
    if state['channel_topic']:
        lines.append(f'Tópico: {state["channel_topic"]}.')
    return '\n'.join(lines)


def trigger_instruction(state: BotState) -> str:
    numbered = '\n'.join(
        _numbered_turn(index, message)
        for index, message in enumerate(recent_messages(state))
    )
    return (
        'Decida se o Maciota entra agora. O padrão é ficar quieto. '
        'O raciocínio vem antes da ação. Entre só quando alguém fala com '
        'ele (pelo nome, xingando, ou respondendo a mensagem dele) ou '
        'quando surge uma fala absurda que ele ainda não comentou. '
        'Fique em silence quando a linha é reação curta (kkk, "que", '
        '"?????"), quando duas pessoas estão se explicando, quando a '
        'fala é pra outra pessoa, ou quando ele já falou daquele gancho. '
        'channel é raro: a sala inteira, sem ninguém pra marcar. reply '
        'só com o índice de uma mensagem de uma pessoa, nunca do próprio '
        'Maciota. O índice começa em 0 na mensagem mais antiga desta '
        'janela.\n'
        f'{numbered}'
    )


def _numbered_turn(index: int, message: object) -> str:
    if isinstance(message, HumanMessage):
        return f'{index}. {message.content}'
    content = getattr(message, 'content', '')
    return f'{index}. Maciota (você): {content}'


def reply_prompt(state: BotState) -> str:
    hook = state['context_hook'] or (
        'nenhum gancho separado; responda à mensagem atual'
    )
    return (
        f'{MACIOTA_PERSONA}\n'
        f'Estilo desta resposta: {state["persona_style"]}.\n'
        f'Gancho: {hook}.\n'
        f'{reply_audience(state)}'
    )


def reply_audience(state: BotState) -> str:
    target = state['reply_to_message_id']
    if target is None:
        return 'Mensagem geral no canal, sem responder uma mensagem específica.'
    author = _author_of(state, target)
    return (
        f'Você está respondendo a mensagem de {author}. '
        'O Discord vai marcar essa mensagem.'
    )


def recent_messages(state: BotState) -> list:
    return list(state['messages'])[-MESSAGE_WINDOW:]


def _author_of(state: BotState, message_id: int) -> str:
    for message in recent_messages(state):
        if not isinstance(message, HumanMessage) or message.id is None:
            continue
        if int(message.id) != message_id:
            continue
        return str(message.content).split(':', 1)[0]
    return 'essa pessoa'
