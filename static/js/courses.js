function markContentComplete(contentId) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(`/conteudo/${contentId}/concluir/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            // Atualiza a barra de progresso
            const progressBar = document.querySelector('.progress-bar');
            progressBar.style.width = `${data.progress}%`;
            progressBar.setAttribute('aria-valuenow', data.progress);
            
            // Marca o item como concluído visualmente
            const contentItem = document.querySelector(`#content-${contentId}`);
            contentItem.classList.add('completed');
            
            // Mostra mensagem de sucesso
            const toast = new bootstrap.Toast(document.querySelector('#successToast'));
            toast.show();
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        const toast = new bootstrap.Toast(document.querySelector('#errorToast'));
        toast.show();
    });
} 