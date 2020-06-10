from rcon.models import UserConfig, enter_session

def _get_conf(sess, key):
    return sess.query(UserConfig).filter(UserConfig.key == key).one_or_none()

def get_user_config(key, default=None):
    with enter_session() as sess:
        res = _get_conf(sess, key)
        return res.value if res else default
    
def _add_conf(sess, key, val):
    return sess.add(UserConfig(
        key=key,
        value=val
    ))

def set_user_config(key, object_):
    with enter_session() as sess:
        conf = _get_conf(sess, key)
        if conf is None:
            _add_conf(sess, key, object_)
        else:
            conf.value = object_
        sess.commit()


class InvalidConfigurationError(Exception):
    pass

class AutoBroadcasts:
    BROADCASTS_RANDOMIZE = 'broadcasts_randomize'
    BROADCASTS_MESSAGES = 'broadcasts_messages'
    BROADCASTS_ENABLED = 'broadcasts_enabled'
    
    def __init__(self):
        pass

    def seed_db(self, sess):
        if _get_conf(sess, self.BROADCASTS_RANDOMIZE) is None:
            _add_conf(sess, self.BROADCASTS_RANDOMIZE, False)
        if _get_conf(sess, self.BROADCASTS_MESSAGES) is None:
            _add_conf(sess, self.BROADCASTS_MESSAGES, [])
        if _get_conf(sess, self.BROADCASTS_ENABLED) is None:
            _add_conf(sess, self.BROADCASTS_ENABLED, False)

    def get_messages(self):
        return get_user_config(self.BROADCASTS_MESSAGES)
    
    def set_messages(self, messages):
        msgs = []

        for m in messages:
            if isinstance(m, str):
                m = m.split(' ', 1)
            if len(m) != 2:
                raise InvalidConfigurationError(
                    "Broacast message must be tuples (<int: seconds>, <str: message>)"
                )
            time, msg = m
            try: 
                time = int(time)
                if time <= 0:
                    raise ValueError("Negative")
            except ValueError as e:
                raise InvalidConfigurationError(
                    "Time must be an positive integer"
                ) from e
            msgs.append((time, msg))

        set_user_config(self.BROADCASTS_MESSAGES, msgs)
        
    def get_randomize(self):
        return get_user_config(self.BROADCASTS_RANDOMIZE)
    
    def set_randomize(self, bool_):
        if not isinstance(bool_, bool):
            raise InvalidConfigurationError("Radomize must be a boolean")
        return set_user_config(self.BROADCASTS_RANDOMIZE, bool_)

    def get_enabled(self):
        return get_user_config(self.BROADCASTS_ENABLED)

    def set_enabled(self, bool_):
        if not isinstance(bool_, bool):
            raise InvalidConfigurationError("Enabled must be a boolean")
        return set_user_config(self.BROADCASTS_ENABLED, bool_)


class AutoRotationPresets:
    ROTATION_PRESETS_KEY = "map_rotation_presets"

    def seed_db(self, sess):
        if _get_conf(sess, self.ROTATION_PRESETS_KEY) is None:
            _add_conf(sess, self.ROTATION_PRESETS_KEY, {})

    def get_rotation_presets(self):
        return get_user_config(self.ROTATION_PRESETS_KEY)

    def set_rotation_presets(self, preset_dict):
        if not preset_dict:
            preset_dict = {}

        if not isinstance(preset_dict, dict):
            raise InvalidConfigurationError("invalid map rotation preset")

        sanitized = {}
        for key, value in preset_dict.items():
            key = str(key)
            if not value:
                value = []
            if not isinstance(value, list):
                raise InvalidConfigurationError("map rotation preset value must be a list")
            sanitized[key] = value

        set_user_config(self.ROTATION_PRESETS_KEY, sanitized)


def seed_default_config():
    with enter_session() as sess:
        AutoBroadcasts().seed_db(sess)
        sess.commit()
    with enter_session() as sess:
        AutoRotationPresets().seed_db(sess)
        sess.commit()
