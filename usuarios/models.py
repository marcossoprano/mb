# usuarios/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError

class UsuarioManager(BaseUserManager):
    def create_user(self, cnpj, nome, telefone=None, email=None, cep=None, rua=None, numero=None, bairro=None, cidade=None, estado=None, password=None):
        if not cnpj:
            raise ValueError('CNPJ é obrigatório')
        
        # Validação: pelo menos email ou telefone deve ser fornecido
        if not email and not telefone:
            raise ValueError('Pelo menos um dos campos: email ou telefone deve ser fornecido')
        
        # Validação: todos os campos de endereço são obrigatórios
        if not all([cep, rua, numero, bairro, cidade, estado]):
            raise ValueError('Todos os campos de endereço são obrigatórios: cep, rua, numero, bairro, cidade, estado')
        
        user = self.model(
            cnpj=cnpj,
            nome=nome,
            telefone=telefone,
            email=self.normalize_email(email) if email else None,
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

    def create_superuser(self, cnpj, nome, telefone=None, email=None, cep=None, rua=None, numero=None, bairro=None, cidade=None, estado=None, password=None):
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
    telefone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    # Campo endereco para compatibilidade com banco existente
    endereco = models.CharField(max_length=255, null=True, blank=True)
    # Campos de endereço detalhado (OBRIGATÓRIOS)
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
    REQUIRED_FIELDS = ['nome', 'cep', 'rua', 'numero', 'bairro', 'cidade', 'estado']

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        # Validação customizada: pelo menos email ou telefone deve ser fornecido
        if not self.email and not self.telefone:
            raise ValidationError('Pelo menos um dos campos: email ou telefone deve ser fornecido')
        
        # Validação: todos os campos de endereço são obrigatórios
        if not all([self.cep, self.rua, self.numero, self.bairro, self.cidade, self.estado]):
            raise ValidationError('Todos os campos de endereço são obrigatórios: cep, rua, numero, bairro, cidade, estado')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_staff(self):
        return self.is_admin

    def endereco_completo(self):
        if all([self.rua, self.numero, self.bairro, self.cidade, self.estado, self.cep]):
            return f"{self.rua}, {self.numero}, {self.bairro}, {self.cidade} - {self.estado}, CEP: {self.cep}"
        return "Endereço incompleto"