import pytest

from maciota_bot.services.welcome import WELCOME_TEMPLATES, build_welcome_message


def test_templates_are_the_eight_welcome_jokes() -> None:
    assert WELCOME_TEMPLATES == (
        '{user_name} entrou. Esconde o controle antes que peça.',
        'Chegou {user_name}. A zueira subiu e ninguém avisou.',
        '{user_name} passou na portaria. A ficha ainda não caiu.',
        'Silêncio na sala: {user_name} chegou pedindo palco.',
        '{user_name} entrou. Podem aplaudir. Ou fingir que não viram.',
        'Olha só: {user_name}. Trouxe desculpa ou só a cara de pau?',
        '{user_name} logou. O grupo tremeu e o lanche sumiu.',
        '{user_name} chegou. Aqui o tapete de boas-vindas é uma casca de banana.',
    )


def test_build_welcome_message_uses_random_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def choice(templates: tuple[str, ...]) -> str:
        seen['templates'] = templates
        return templates[3]

    monkeypatch.setattr('maciota_bot.services.welcome.random.choice', choice)

    text = build_welcome_message('Ada')

    assert seen['templates'] == WELCOME_TEMPLATES
    assert text == WELCOME_TEMPLATES[3].replace('{user_name}', 'Ada')


@pytest.mark.parametrize('template', WELCOME_TEMPLATES)
def test_each_template_substitutes_the_user_name(
    template: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        'maciota_bot.services.welcome.random.choice',
        lambda templates: template,
    )

    text = build_welcome_message('Ada')

    assert text == template.replace('{user_name}', 'Ada')
    assert '{user_name}' not in text


def test_build_welcome_message_keeps_braces_in_the_user_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        'maciota_bot.services.welcome.random.choice',
        lambda templates: templates[0],
    )

    text = build_welcome_message('a{b}')

    assert 'a{b}' in text
    assert '{user_name}' not in text
