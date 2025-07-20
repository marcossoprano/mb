# usuarios/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UsuarioManager(BaseUserManager):
    def create_user(self, cnpj, nome, telefone, email, cep, rua, numero, bairro, cidade, estado, password=None):
        if not cnpj:
            raise ValueError('CNPJ é obrigatório')
        user = self.model(
            cnpj=cnpj,
            nome=nome,
            telefone=telefone,
            email=self.normalize_email(email),
            cep=cep,
            rua=rua,
            numero=numero,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, cnpj, nome, telefone, email, cep, rua, numero, bairro, cidade, estado, password):
        user = self.create_user(
            cnpj=cnpj,
            nome=nome,
            telefone=telefone,
            email=email,
            cep=cep,
            rua=rua,
            numero=numero,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class Usuario(AbstractBaseUser):
    cnpj = models.CharField(max_length=18, unique=True, primary_key=True)
    nome = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    cep = models.CharField(max_length=8)
    rua = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'cnpj'
    REQUIRED_FIELDS = ['nome', 'telefone', 'email', 'cep', 'rua', 'numero', 'bairro', 'cidade', 'estado']

    def __str__(self):
        return self.nome

    @property
    def is_staff(self):
        return self.is_admin

    def endereco_completo(self):
        return f"{self.rua}, {self.numero}, {self.bairro}, {self.cidade} - {self.estado}, CEP: {self.cep}"