from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix="SDP_REMOTE",
    settings_files=['settings.toml', '.secrets.toml'],
    validators=[
        Validator('intro', default='sdpremote', is_type_of=str),
    ],
)
