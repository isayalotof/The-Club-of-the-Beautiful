// JavaScript для админ-панели
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех DataTables
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        if (table.id) {
            try {
                new DataTable(`#${table.id}`, {
                    language: {
                        url: '//cdn.datatables.net/plug-ins/1.13.1/i18n/ru.json'
                    },
                    responsive: true
                });
            } catch (e) {
                console.error(`Ошибка инициализации таблицы #${table.id}:`, e);
            }
        }
    });

    // Показывать имя выбранного файла при загрузке изображений
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'Файл не выбран';
            const label = this.nextElementSibling || this.closest('.form-group').querySelector('label');
            if (label) {
                label.innerText = fileName;
            }
        });
    });

    // Обработка формы с подтверждением
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Переключение чекбоксов для удаления изображений
    const removeImageCheckboxes = document.querySelectorAll('input[name="remove_image"]');
    removeImageCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const imageInput = this.closest('.mb-3').querySelector('input[type="file"]');
            if (this.checked) {
                if (imageInput) {
                    imageInput.disabled = true;
                }
                const previewContainer = this.closest('.mb-3').querySelector('#current_image_container');
                if (previewContainer) {
                    previewContainer.style.opacity = 0.5;
                }
            } else {
                if (imageInput) {
                    imageInput.disabled = false;
                }
                const previewContainer = this.closest('.mb-3').querySelector('#current_image_container');
                if (previewContainer) {
                    previewContainer.style.opacity = 1;
                }
            }
        });
    });
});