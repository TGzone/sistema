document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. SELEÇÃO DE ELEMENTOS ---
    const cnpjInput = document.getElementById('cnpjMask');
    const phoneInput = document.getElementById('phoneMask');
    const cepInput = document.getElementById('cep'); // ID usado na busca ViaCEP

    // --- 2. FUNÇÃO AUXILIAR: LIMPAR ENDEREÇO ---
    const limpa_formulário_cep = () => {
        document.getElementById('logradouro').value = "";
        document.getElementById('bairro').value = "";
        document.getElementById('localidade').value = "";
        document.getElementById('uf').value = "";
    };

    // --- 3. MÁSCARA DE CNPJ ---
    if (cnpjInput) {
        cnpjInput.addEventListener('input', e => {
            let v = e.target.value.replace(/\D/g, '');
            v = v.replace(/^(\d{2})(\d)/, "$1.$2");
            v = v.replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3");
            v = v.replace(/\.(\d{3})(\d)/, ".$1/$2");
            v = v.replace(/(\d{4})(\d)/, "$1-$2");
            e.target.value = v.substring(0, 18);
        });
    }

    // --- 4. MÁSCARA DE TELEFONE ---
    if (phoneInput) {
        phoneInput.addEventListener('input', e => {
            let v = e.target.value.replace(/\D/g, '');
            v = v.replace(/^(\d{2})(\d)/g, "($1) $2");
            v = v.replace(/(\d)(\d{4})$/, "$1-$2");
            e.target.value = v.substring(0, 15);
        });
    }

    // --- 5. BUSCA VIACEP (ACIONADA AO SAIR DO CAMPO CEP) ---
    if (cepInput) {
        // Máscara simples para o CEP enquanto digita
        cepInput.addEventListener('input', e => {
            let v = e.target.value.replace(/\D/g, '');
            v = v.replace(/^(\d{5})(\d)/, "$1-$2");
            e.target.value = v.substring(0, 9);
        });

        // Lógica de busca na API
        cepInput.addEventListener('blur', function() {
            let cep = this.value.replace(/\D/g, '');

            if (cep !== "") {
                let validacep = /^[0-9]{8}$/;

                if(validacep.test(cep)) {
                    // Feedback visual de carregamento
                    document.getElementById('logradouro').value = "...";
                    document.getElementById('bairro').value = "...";
                    document.getElementById('localidade').value = "...";
                    document.getElementById('uf').value = "...";

                    fetch(`https://viacep.com.br/ws/${cep}/json/`)
                        .then(response => response.json())
                        .then(dados => {
                            if (!("erro" in dados)) {
                                document.getElementById('logradouro').value = dados.logradouro;
                                document.getElementById('bairro').value = dados.bairro;
                                document.getElementById('localidade').value = dados.localidade;
                                document.getElementById('uf').value = dados.uf;
                                
                                // Foca no número automaticamente
                                const numInput = document.getElementsByName('numero')[0];
                                if(numInput) numInput.focus();
                            } else {
                                limpa_formulário_cep();
                                alert("CEP não encontrado.");
                            }
                        })
                        .catch(() => {
                            limpa_formulário_cep();
                            alert("Erro ao consultar o servidor ViaCEP.");
                        });
                } else {
                    limpa_formulário_cep();
                    alert("Formato de CEP inválido.");
                }
            }
        });
    }
});