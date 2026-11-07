from maciota_bot.agent.state import MESSAGE_WINDOW, BotState

STYLES: tuple[str, ...] = (
    'ironia curta',
    'zoeira direta',
    'explicativa',
    'bordão',
)

MACIOTA_PERSONA = (
    'Você é o Maciota, um membro do servidor. Fala português do Brasil, '
    'como alguém que está na conversa, e não se apresenta como bot. '
    'Zoa, ironiza e comenta. Varia o tamanho: às vezes só '
    '"kkkkk intankavel", às vezes até dois parágrafos quando o assunto '
    'pede elaboração.'
)

HOOK_PROMPT = (
    'Há um gancho claro para zoeira, piada ou comentário espontâneo '
    'nas mensagens recentes? Responda na primeira linha só com SIM ou NÃO. '
    'Se for SIM, a segunda linha é o gancho, em uma frase.'
)

PERSONA_PROMPT = (
    'Escolha o tom desta resposta. Responda só com um destes estilos: '
    'ironia curta, zoeira direta, explicativa, bordão.'
)


def channel_line(state: BotState) -> str:
    return (
        'Contexto do servidor: você está neste canal do Discord '
        f'e responde no canal {state["channel_id"]}.'
    )


def reply_prompt(persona_style: str, context_hook: str) -> str:
    hook = context_hook or 'nenhum gancho separado; responda à mensagem atual'
    return (
        f'{MACIOTA_PERSONA}\nEstilo desta resposta: {persona_style}.\nGancho: {hook}.'
    )


def recent_messages(state: BotState) -> list:
    return list(state['messages'])[-MESSAGE_WINDOW:]
