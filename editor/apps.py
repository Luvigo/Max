from django.apps import AppConfig


class EditorConfig(AppConfig):
    name = 'editor'

    def ready(self):
        import editor.signals  # noqa: F401 - Registra post_save para auto-crear perfiles
