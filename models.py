
class Serialiser(object):
    def get_object(self):
        ret = {}
        for v in self.get_attr_list():
            ret[v] = getattr(self, v)
        return ret

    def __repr__(self):
        parts = []
        for v in self.get_attr_list():
            parts.append("%s: '%s'" % (v, getattr(self, v)))
        return ", ".join(parts)

    @classmethod
    def object_from_data(cls, data):
        o = cls()
        for k,v in data.iteritems():
            setattr(o, k, v)
        return o

class User(Serialiser):
    username = ""
    date_joined = ""
    key = ""
    secret = ""
    def get_attr_list(self):
        return ["username", "date_joined", "key", "secret"]

class Song(Serialiser):
    pass

class Share(Serialiser):
    pass

class Want(Serialiser):
    pass

class Play(Serialiser):
    pass
