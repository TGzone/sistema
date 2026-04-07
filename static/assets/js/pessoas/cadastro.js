const peopleModule = {
    init: function() {
        this.initFilters();
        this.initDrawer();
        this.initSearch();
        this.initRegistrationLogic();
        this.initIgrejaSearch();
        this.initVenculoLogic(); // Chamando a nova função
    },

    initFilters: function() { /* Mantido */ },
    initDrawer: function() { /* Mantido */ },
    initSearch: function() { /* Mantido */ },

    initRegistrationLogic: function() {
        const selectTipo = document.getElementById('tipoPessoa');
        const groupResponsavel = document.getElementById('groupResponsavel');
        const cepInput = document.getElementById('cepMask');
        const phoneInput = document.getElementById('phoneMask');

        if (selectTipo && groupResponsavel) {
            selectTipo.addEventListener('change', (e) => {
                groupResponsavel.style.display = (e.target.value === 'kids') ? 'block' : 'none';
            });
        }

        if (phoneInput) {
            phoneInput.addEventListener('input', e => {
                let v = e.target.value.replace(/\D/g, '');
                v = v.replace(/^(\d{2})(\d)/g, "($1) $2");
                v = v.replace(/(\d)(\d{4})$/, "$1-$2");
                e.target.value = v.substring(0, 15);
            });
        }

        if (cepInput) {
            cepInput.addEventListener('input', e => {
                let v = e.target.value.replace(/\D/g, '');
                v = v.replace(/^(\d{5})(\d)/, "$1-$2");
                e.target.value = v.substring(0, 9);
            });

            cepInput.addEventListener('blur', () => {
                const cep = cepInput.value.replace(/\D/g, '');
                if (cep.length === 8) {
                    this.setAddressFields("...");
                    fetch(`https://viacep.com.br/ws/${cep}/json/`)
                        .then(response => response.json())
                        .then(dados => {
                            if (!("erro" in dados)) {
                                document.getElementById('logradouro').value = dados.logradouro;
                                document.getElementById('bairro').value = dados.bairro;
                                document.getElementById('localidade').value = dados.localidade;
                                document.getElementById('uf').value = dados.uf;
                                const numInput = document.getElementById('numero');
                                if(numInput) numInput.focus();
                            } else {
                                this.setAddressFields("");
                                alert("CEP não encontrado.");
                            }
                        })
                        .catch(() => {
                            this.setAddressFields("");
                            alert("Erro ao consultar o servidor ViaCEP.");
                        });
                }
            });
        }
    },

    initIgrejaSearch: function() {
        const input = document.getElementById('igrejaSearch');
        const hiddenInput = document.getElementById('unidade_id_hidden');
        const datalist = document.getElementById('igrejasList');

        if (input && datalist) {
            input.addEventListener('input', function() {
                const val = this.value;
                const options = datalist.options;
                hiddenInput.value = ""; 

                for (let i = 0; i < options.length; i++) {
                    if (options[i].value === val) {
                        hiddenInput.value = options[i].getAttribute('data-id');
                        break;
                    }
                }
            });
            
            input.addEventListener('blur', function() {
                if (this.value === "") hiddenInput.value = "";
            });
        }
    },

    initVenculoLogic: function() {
        const checkbox = document.getElementById('membroCheck');
        const unidadeGroup = document.getElementById('unidadeGroup');
        const igrejaSearch = document.getElementById('igrejaSearch');
        const hiddenInput = document.getElementById('unidade_id_hidden');
        
        // Pegamos o ID que o Django já colocou no value do input hidden ao carregar
        const idInicial = hiddenInput ? hiddenInput.value : "";

        if (checkbox && unidadeGroup) {
            const alternarCampos = () => {
                if (checkbox.checked) {
                    unidadeGroup.style.display = 'none'; 
                    hiddenInput.value = idInicial; 
                } else {
                    unidadeGroup.style.display = 'block'; 
                    igrejaSearch.value = ""; 
                    hiddenInput.value = ""; 
                }
            };

            checkbox.addEventListener('change', alternarCampos);
            alternarCampos(); 
        }
    },

    setAddressFields: function(value) {
        const fields = ['logradouro', 'bairro', 'localidade', 'uf'];
        fields.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = value;
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    peopleModule.init();
});