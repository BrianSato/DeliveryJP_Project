# 🛒 Sistema de Pedidos com Controle de Estoque por Lote

Este projeto é uma aplicação web desenvolvida com Django para gerenciamento de pedidos, incluindo controle de estoque por lote e automação de expiração de pedidos.

O objetivo é aplicar boas práticas de desenvolvimento backend, modelagem de dados e regras de negócio reais.

---

## 🎥 Demonstração do Sistema

Demonstração completa do fluxo de pedidos, controle de estoque por lote e expiração automática.

[![Assista ao vídeo](https://img.youtube.com/vi/cn1a08gz9YQ/0.jpg)](https://www.youtube.com/watch?v=cn1a08gz9YQ)

---

## 🏪 Contexto do Projeto (Acadêmico)

Este sistema foi desenvolvido com base em um cenário real, utilizando como referência uma loja existente, com autorização para uso de imagem para fins acadêmicos.

A aplicação foi projetada simulando um ambiente real de operação, incluindo regras de negócio como controle de estoque por lote e gestão de expiração de pedidos.

---

## 🚀 Funcionalidades

### 📦 Pedidos
- Criação de pedidos
- Associação de múltiplos itens ao pedido
- Cálculo automático de valores
- Controle de status do pedido

### 🧾 Itens do Pedido
- Registro de produtos no momento da compra
- Persistência de nome e tipo do produto (histórico)
- Quantidade e valor unitário

### 📊 Estoque por Lote
- Controle de produtos por lote
- Baixa automática de estoque ao criar pedidos
- Prevenção de venda sem estoque suficiente

### ⏳ Expiração de Pedidos
- Definição de data limite para pagamento
- Atualização automática de status para "expirado"
- Lógica baseada em data

---

## 🧠 Regras de Negócio Implementadas

- Um pedido pode conter múltiplos itens
- O estoque é controlado por lote (não apenas produto)
- Ao criar um pedido:
  - O sistema valida disponibilidade em estoque
  - Realiza a baixa automaticamente
- Pedidos podem expirar com base na data limite

---

## 🏗️ Arquitetura

O projeto segue uma separação de responsabilidades baseada em:

- Models: definição das entidades e regras de dados
- Views: controle das requisições e respostas
- Services: regras de negócio isoladas (quando aplicável)
- Signals: automações e eventos do sistema

Essa abordagem facilita a manutenção, escalabilidade e organização do código.

---

## 🛠️ Tecnologias Utilizadas

- Python 3
- Django
- SQLite (ambiente de desenvolvimento)
- HTML / CSS
- JavaScript (validações e formatação)
- Render (deploy)
---

## ⚙️ Como Executar o Projeto

### 1. Clone o repositório
```bash
git clone (https://github.com/BrianSato/DeliveryJP_Project.git
cd DeliveryJP_Project
```
### 2. Crie e ative o ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```
### 3. Instale as dependências
```bash
pip install -r requirements.txt
```
### 4.Execute as migrações
```bash
python manage.py migrate
```
### 5.Crie um superusuário
```bash
python manage.py createsuperuser
```
### 6.Rode o servidor
```bash
python manage.py runserver
```
---
## 🔐 Acesso ao Admin

### Acesse:
```bash
http://127.0.0.1:8000/admin/
```
---

## 📁 Estrutura do Projeto
```bash
core/
├── models.py
├── views.py
├── services.py  # (se aplicável)
├── signals.py   # (se estiver usando automações)
```
---

## 📌 Melhorias Futuras

 - Dashboard com estatísticas
   
 - Interface mais amigável (UI/UX)
   
 - API REST com Django REST Framework
   
 - Testes automatizados

 ---
 
## 👨‍💻 Autor

Desenvolvido por Brian Sato

GitHub: https://github.com/BrianSato
LinkedIn: https://www.linkedin.com/in/brian-sato-b16563263/

---

## 📄 Licença

Este projeto é apenas para fins de estudo e portfólio.








