# DJ LMS
![Badge em Desenvolvimento](http://img.shields.io/static/v1?label=STATUS&message=EM%20DESENVOLVIMENTO&color=GREEN&style=for-the-badge)

## 🎯 Sobre o Projeto

Este sistema foi baseado no conceito de LMS (Learning Management System), ou Sistema de Gestão de Aprendizagem, que busca facilitar a criação, gerenciamento e acompanhamento de cursos online. Seguindo essa ideia, a plataforma oferece recursos como gestão de cursos, avaliações, eventos, gamificação e muito mais.

## ⚙️ Funcionalidades

### Sistema de Autenticação e Usuários
- Login/Registro com email
- Autenticação via redes sociais
- Perfis de usuário
- Controle de permissões
- Recuperação de senha

### Sistema de Cursos
- Criação e gestão de cursos
- Módulos e lições
- Progresso do aluno
- Material complementar
- Discussões

### Sistema de Gamificação
- Sistema de pontos
- Conquistas/Badges
- Rankings
- Desafios
- Recompensas

### Sistema de Avaliações
- Diferentes tipos de questões
- Correção automática
- Feedback personalizado
- Banco de questões
- Relatórios de desempenho

### Sistema de Eventos
- Webinars
- Workshops
- Calendário integrado
- Inscrições
- Certificados

### Sistema de Conteúdo
- Editor rico WYSIWYG
- Versionamento
- Sistema de revisão
- Importação/Exportação
- Gestão de mídia

### Sistema de API REST
- Endpoints RESTful
- Autenticação via Token
- Rate limiting
- Documentação OpenAPI
- Versionamento

## 🛠️ Tecnologias Utilizadas

- Python 3.8+
- Django 4.2
- Django REST Framework
- PostgreSQL

## 🚀 Configuração do Ambiente

1. Clone o repositório:
```powershell
git clone https://github.com/seu-usuario/learning-system.git
cd learning-system
```

2. Crie e ative o ambiente virtual:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

3. Instale as dependências:
```powershell
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```powershell
copy .env.example .env
```

5. Execute as migrações:
```powershell
python manage.py migrate
```

6. Crie um superusuário:
```powershell
python manage.py createsuperuser
```

7. Inicie o servidor:
```powershell
python manage.py runserver
```

## 📁 Estrutura do Projeto

```
learning_system/
├── accounts/            # Sistema de autenticação
├── courses/             # Sistema de cursos
├── assessments/         # Sistema de avaliações
├── events/              # Sistema de eventos
├── content/             # Sistema de conteúdo
├── gamification/        # Sistema de gamificação
├── api/                 # API REST
├── static/             # Arquivos estáticos
├── templates/          # Templates HTML
├── media/              # Uploads de usuários
└── config/             # Configurações do projeto
```

## 📚 API Documentation

### Autenticação

```http
POST /api/auth/token/
Content-Type: application/json

{
    "username": "user@email.com",
    "password": "senha123"
}
```

### Endpoints Principais

#### Cursos
- `GET /api/courses/` - Lista todos os cursos
- `POST /api/courses/` - Cria novo curso
- `GET /api/courses/{id}/` - Detalhes do curso
- `PUT /api/courses/{id}/` - Atualiza curso
- `DELETE /api/courses/{id}/` - Remove curso
- `POST /api/courses/{id}/enroll/` - Matricula usuário

#### Eventos
- `GET /api/events/` - Lista eventos
- `POST /api/events/` - Cria evento
- `GET /api/events/{id}/` - Detalhes do evento
- `POST /api/events/{id}/register/` - Registra participante

#### Avaliações
- `GET /api/assessments/` - Lista avaliações
- `POST /api/assessments/` - Cria avaliação
- `POST /api/assessments/{id}/submit/` - Submete respostas

### Rate Limiting
- Anônimo: 60/minuto, 1000/dia
- Autenticado: 120/minuto, 5000/dia

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📊 Status do Projeto

### Implementado ✅
- Sistema de Autenticação e Usuários
- Sistema de Cursos
- Sistema de Gamificação
- Sistema de Certificados
- Sistema de Recomendações
- Sistema de Analytics
- Sistema de Notificações
- Sistema de Avaliações
- Sistema de Conteúdo
- Sistema de Eventos
- API REST

### Em Desenvolvimento 🚧
- Sistema de Suporte
- Sistema de Internacionalização
- Aplicativo Mobile
- Integrações com terceiros

## 📞 Suporte

Em caso de dúvidas ou problemas:
- Abra uma issue
- Email: ...
- Discord: [https://discord.gg/km2yqJzs]
