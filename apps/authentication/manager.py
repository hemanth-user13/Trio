from django.contrib.auth.base_user import BaseUserManager



class UserManager(BaseUserManager):


    use_in_migrations=True

    def _create_user(self,phone_number,password=None,**extra_fields):
        if not phone_number:
            raise ValueError("the phone number must be set")
        email=extra_fields.get("email")
        extra_fields["email"]=self.normalize_email(email).lower() if email else None

        user=self.model(phone_number=phone_number,**extra_fields)

        if password:
            user.set_password(password)

        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user


    def create_user(self,phone_number,password=None,**extra_args):
        extra_args.setdefault("is_staff",False)
        extra_args.setdefault("is_superuser",False)
        return self._create_user(phone_number,password,**extra_args)

    def create_superuser(self,phone_number,password=None,**extrargs):
        extrargs.setdefault("is_staff",True)
        extrargs.setdefault("is_superuser",True)
        extrargs.setdefault("is_phone_verified",True)


        if not password:
            raise ValueError("Superuser must have password ")
        if extrargs.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff as True")
        if extrargs.get("is_superuser") is not True:
            raise ValueError("superuser must have is_superuser as True")

        return self._create_user(phone_number,password,**extrargs)