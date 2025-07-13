"""
Script para demonstrar a diferença entre configurações de tempo de token
"""

# CONFIGURAÇÃO ANTERIOR (5 minutos)
CONFIG_ANTERIOR = {
    "ACCESS_TOKEN_LIFETIME": "5 minutos",
    "REFRESH_TOKEN_LIFETIME": "1 dia",
    "Tempo_para_testes": "Muito curto - precisa renovar constantemente"
}

# CONFIGURAÇÃO ATUAL (24 horas)
CONFIG_ATUAL = {
    "ACCESS_TOKEN_LIFETIME": "24 horas", 
    "REFRESH_TOKEN_LIFETIME": "30 dias",
    "Tempo_para_testes": "Muito prático - pode testar por horas"
}

print("=== COMPARAÇÃO DE CONFIGURAÇÕES ===")
print()
print("CONFIGURAÇÃO ANTERIOR:")
for key, value in CONFIG_ANTERIOR.items():
    print(f"  {key}: {value}")
print()
print("CONFIGURAÇÃO ATUAL:")
for key, value in CONFIG_ATUAL.items():
    print(f"  {key}: {value}")
print()
print("=== COMO TESTAR NO POSTMAN ===")
print()
print("1. Faça login uma vez:")
print("   POST /api/usuarios/login/")
print("   Body: {\"cnpj\": \"seu_cnpj\", \"password\": \"sua_senha\"}")
print()
print("2. Use o access_token por 24 horas:")
print("   Authorization: Bearer seu_access_token")
print()
print("3. Verifique quando expira:")
print("   GET /api/usuarios/info-token/")
print("   Authorization: Bearer seu_access_token")
print()
print("4. Se precisar renovar:")
print("   POST /api/usuarios/token/refresh/")
print("   Body: {\"refresh\": \"seu_refresh_token\"}")
print()
print("=== VANTAGENS DA NOVA CONFIGURAÇÃO ===")
print("✅ Token dura 24 horas (não 5 minutos)")
print("✅ Pode testar por horas sem renovar")
print("✅ Refresh token dura 30 dias")
print("✅ Muito mais prático para desenvolvimento") 