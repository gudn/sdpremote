from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix="SDP_REMOTE",
    settings_files=['settings.toml', '.secrets.toml'],
    validators=[
        Validator('intro', default='sdpremote', is_type_of=str),
        Validator('debug', default=False, is_type_of=bool),
        Validator('database.uri', must_exist=True, is_type_of=str),
        Validator('storage.endpoint', must_exist=True, is_type_of=str),
        Validator('storage.port', must_exist=True, is_type_of=int),
        Validator('storage.secure', default=False, is_type_of=bool),
        Validator('storage.region', must_exist=True, is_type_of=str),
        Validator('storage.access_key', must_exist=True, is_type_of=str),
        Validator('storage.secret_key', must_exist=True, is_type_of=str),
    ],
)
