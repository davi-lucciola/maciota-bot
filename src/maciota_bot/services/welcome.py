import random

WELCOME_TEMPLATES: tuple[str, ...] = (
    '{user_name} entrou. Esconde o controle antes que peça.',
    'Chegou {user_name}. A zueira subiu e ninguém avisou.',
    '{user_name} passou na portaria. A ficha ainda não caiu.',
    'Silêncio na sala: {user_name} chegou pedindo palco.',
    '{user_name} entrou. Podem aplaudir. Ou fingir que não viram.',
    'Olha só: {user_name}. Trouxe desculpa ou só a cara de pau?',
    '{user_name} logou. O grupo tremeu e o lanche sumiu.',
    '{user_name} chegou. Aqui o tapete de boas-vindas é uma casca de banana.',
)


def build_welcome_message(user_name: str) -> str:
    template = random.choice(WELCOME_TEMPLATES)
    return template.replace('{user_name}', user_name)
