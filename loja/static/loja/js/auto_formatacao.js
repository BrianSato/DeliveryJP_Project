
document.addEventListener('DOMContentLoaded', function () {
    const telefoneInput = document.getElementById('telefone');

    if (!telefoneInput) return;

    telefoneInput.addEventListener('input', function (e) {
        let value = e.target.value;

        // remove tudo que não é número
        value = value.replace(/\D/g, '');

        // limita a 11 dígitos
        value = value.slice(0, 11);

        // formata
        if (value.length <= 3) {
            e.target.value = value;
        } else if (value.length <= 7) {
            e.target.value = value.slice(0, 3) + '-' + value.slice(3);
        } else {
            e.target.value =
                value.slice(0, 3) + '-' +
                value.slice(3, 7) + '-' +
                value.slice(7);
        }
    });

    //  bloqueia letras na digitação
    telefoneInput.addEventListener('keypress', function (e) {
        if (!/[0-9]/.test(e.key)) {
            e.preventDefault();
        }
    });
});