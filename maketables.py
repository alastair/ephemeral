from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models

engine = create_engine('mysql://ephemeral:fdsov08*(y7fkjfdskirujfs093r@localhost/ephemeral')
DbSession = sessionmaker(bind=engine)
session = DbSession()

models.Base.metadata.create_all(engine)

u = models.User()
u.screen_name = "ephemeralplayback"
session.add(u)
#session.commit()

