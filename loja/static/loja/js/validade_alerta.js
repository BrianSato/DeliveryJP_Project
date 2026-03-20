
document.addEventListener('DOMContentLoaded',function () {
    document.addEventListener('submit', function (event) {
        const campos = document.querySelectorAll('[id$=data_validade]');
        let existeCampoPreenchido = false;
        let existeCampoVazio = false;
        campos.forEach(function (campo) {
            //ignora campos escondidos ou desabilitador
            if (campo.offsetParent === null || campo.disable) {
                return;
            }
            if (campo.value && campo.value.trim() !== '') {
                existeCampoPreenchido = true;
            } else {
                existeCampoVazio = true;
            }
        });
        //só alerta se todos estiverem vazios
        if (!existeCampoPreenchido && existeCampoVazio) {
            const confirmar = confirm(
                '⚠ Este produto está sem data de validade.\n' +
                'Deseja salvar mesmo assim?'
            );
            if (!confirmar) {
                event.preventDefault();
            }
        }
    });
});
