document.addEventListener('DOMContentLoaded', function() {

    const tipoSelect = document.getElementById('tipo');
    const campoProduto = document.getElementById('campo-produto');
    const campoNome = document.getElementById('campo-nome-produto');
    const campoValor = document.getElementById('campo-valor');

    if (!tipoSelect) return; // evita erro se não estiver na página

    function atualizarCampos() {
        if (tipoSelect.value === 'ESTOQUE') {
            campoProduto.style.display = 'block';
            campoNome.style.display = 'none';
            campoValor.style.display = 'none';
        } else {
            campoProduto.style.display = 'none';
            campoNome.style.display = 'block';
            campoValor.style.display = 'block';
        }
    }

    tipoSelect.addEventListener('change', atualizarCampos);

    atualizarCampos();
});