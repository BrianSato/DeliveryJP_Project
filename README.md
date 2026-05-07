# 🛒 Sistema de Pedidos com Controle de Estoque por Lote

Sistema web desenvolvido com Django para gerenciamento de pedidos, encomendas e controle de estoque por lote, simulando regras de negócio aplicadas em um ambiente real de operação comercial.

O projeto foi desenvolvido com foco em boas práticas de desenvolvimento backend, organização de arquitetura, modelagem de dados e implementação de regras de negócio reais.

---

# 🎥 Demonstração do Sistema

Demonstração completa do fluxo de pedidos, controle de estoque por lote, integração entre módulos e gerenciamento de encomendas.

[![Assista ao vídeo](https://img.youtube.com/vi/Ywl3XgbpXKU/0.jpg)](https://www.youtube.com/watch?v=Ywl3XgbpXKU)

---

# 🏪 Contexto do Projeto (Acadêmico)

Este sistema foi desenvolvido com base em um cenário real, utilizando como referência uma loja existente, com autorização para uso de imagem para fins acadêmicos.

A aplicação foi projetada simulando um ambiente real de operação, incluindo funcionalidades como:

- Controle de estoque por lote
- Gestão de pedidos e encomendas
- Controle de produtos ativos/inativos
- Validações de estoque
- Expiração automática de pedidos
- Integração entre estoque e vendas

---

# 🚀 Funcionalidades

## 📦 Pedidos
- Criação de pedidos
- Associação de múltiplos itens ao pedido
- Cálculo automático de valores
- Controle de status do pedido
- Expiração automática de pedidos

## 🧾 Itens do Pedido
- Registro individual dos produtos vendidos
- Persistência de histórico de nome e tipo do produto
- Controle de quantidade e valor unitário

## 📊 Controle de Estoque por Lote
- Controle separado por lote
- Baixa automática de estoque
- Validação de disponibilidade
- Atualização automática de quantidades
- Prevenção de venda sem estoque suficiente

## 📋 Sistema de Encomendas
- Registro de produtos encomendados
- Controle separado entre pedidos e encomendas
- Organização de múltiplos itens relacionados à mesma encomenda

## 🔄 Integração e Validações
- Atualização automática entre módulos
- Consistência entre estoque e pedidos
- Controle de produtos ativos e inativos
- Correções automáticas de inconsistências

---

# 🧠 Regras de Negócio Implementadas

- Um pedido pode conter múltiplos itens
- O estoque é controlado por lote
- O sistema valida disponibilidade antes da venda
- A baixa de estoque ocorre automaticamente
- Produtos inativos não podem ser vendidos
- Pedidos podem expirar automaticamente
- O sistema mantém histórico de produtos vendidos
- Encomendas possuem controle separado do fluxo padrão de vendas

---

# 🏗️ Arquitetura e Organização do Projeto

O projeto foi estruturado com foco na separação de responsabilidades, utilizando um app principal chamado `loja`, responsável por centralizar as regras de negócio do sistema.

```bash
loja/
├── models.py       # definição das entidades e estrutura do banco
├── views.py        # controle das requisições e respostas
├── urls.py         # roteamento da aplicação
├── services.py     # regras de negócio
├── signals.py      # automações e eventos do sistema
├── utils.py        # funções auxiliares
├── middleware.py   # interceptação e controle de requisições
```

---

Outras estruturas relevantes:

```bash
templates/loja/   # páginas HTML do sistema
static/loja/      # arquivos estáticos (CSS, JavaScript e imagens)
```

Essa organização foi adotada para facilitar:

manutenção;
escalabilidade;
reaproveitamento de código;
clareza na separação de responsabilidades.

---


# 🛠️ Tecnologias Utilizadas
- Python 3
  
- Django
  
- PostgreSQL (produção)
  
- SQLite (desenvolvimento)
  
- HTML5
  
- CSS3
  
- JavaScript

- Bootstrap
  
- Render (deploy)
  
- Git/GitHub

---


⚙️ Como Executar o Projeto
1. Clone o repositório:

```bash
git clone https://github.com/BrianSato/DeliveryJP_Project.git
cd DeliveryJP_Project
```
2. Crie e ative o ambiente virtual
Linux/macOS:
```bash
python -m venv venv
source venv/bin/activate
```
Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

---

3. Instale as dependências
```bash
pip install -r requirements.txt
```

---

4. Execute as migrações
```bash
python manage.py migrate
```

---

5. Crie um superusuário
```bash
python manage.py runserver
```

---

# 🔐 Acesso ao Admin
```bash
http://127.0.0.1:8000/admin/
```

---

# 🌐 Deploy

O sistema foi publicado utilizando:

- PostgreSQL para banco de dados em produção
  
- Hospedagem via Render

---

# 📌 Melhorias Futuras
- Dashboard com estatísticas
  
- Relatórios financeiros
  
- API REST com Django REST Framework
  
- Melhorias de UI/UX
  
- Sistema de autenticação avançado
  
- Controle de permissões de usuários

---


# 👨‍💻 Autor

Desenvolvido por Brian Sato

GitHub:
https://github.com/BrianSato

LinkedIn:
https://www.linkedin.com/in/brian-sato-b16563263/

# 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos, estudo e portfólio.








