document.addEventListener('DOMContentLoaded', function() {

    const tipoSelect = document.getElementById('tipo');
    const campoProduto = document.getElementById('campo-produto');
    const campoNome = document.getElementById('campo-nome-produto');
    const campoValor = document.getElementById('campo-valor');

    const inputValor = document.querySelector('[name="valor_unitario"]');
    const inputNome = document.querySelector('[name="nome_produto"]');

    if (!tipoSelect) return;

    function atualizarCampos() {
        if (tipoSelect.value === 'ESTOQUE') {
            campoProduto.style.display = 'block';
            campoNome.style.display = 'none';
            campoValor.style.display = 'none';

            // REMOVE obrigatoriedade
            if (inputValor) inputValor.required = false;
            if (inputNome) inputNome.required = false;

        } else { // ENCOMENDA
            campoProduto.style.display = 'none';
            campoNome.style.display = 'block';
            campoValor.style.display = 'block';

            // TORNA obrigatório
            if (inputValor) inputValor.required = true;
            if (inputNome) inputNome.required = true;
        }
    }

    tipoSelect.addEventListener('change', atualizarCampos);

    atualizarCampos();
});