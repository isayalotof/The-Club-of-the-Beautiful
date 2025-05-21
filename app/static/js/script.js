/**
 * Общие функции для сайта салона красоты
 */

// Функция для отображения сообщений
function showMessage(message, type = 'success') {
    const alertPlaceholder = document.getElementById('alert-placeholder');
    if (!alertPlaceholder) return;

    const wrapper = document.createElement('div');
    wrapper.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show');
    wrapper.setAttribute('role', 'alert');
    wrapper.innerHTML = `
        <div>${message}</div>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Закрыть"></button>
    `;

    alertPlaceholder.appendChild(wrapper);

    // Автоматически скрываем сообщение через 5 секунд
    setTimeout(() => {
        if (wrapper.parentNode) {
            wrapper.classList.remove('show');
            setTimeout(() => {
                wrapper.parentNode.removeChild(wrapper);
            }, 150);
        }
    }, 5000);
}

// Функция для отправки данных на сервер
async function sendData(url, method, data) {
    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Что-то пошло не так');
        }

        return await response.json();
    } catch (error) {
        throw error;
    }
}

// Функция для загрузки услуг
async function loadServices(category = '', sort = '', page = 1) {
    try {
        const url = `/api/services?category=${category}&sort=${sort}&page=${page}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Не удалось загрузить услуги');
        }
        return await response.json();
    } catch (error) {
        console.error('Ошибка при загрузке услуг:', error);
        showMessage('Не удалось загрузить услуги. Пожалуйста, попробуйте позже.', 'danger');
    }
}

// Функция для загрузки записей
async function loadAppointments(status = '') {
    try {
        const url = `/api/appointments/my?status=${status}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Не удалось загрузить записи');
        }
        return await response.json();
    } catch (error) {
        console.error('Ошибка при загрузке записей:', error);
        showMessage('Не удалось загрузить ваши записи. Пожалуйста, попробуйте позже.', 'danger');
    }
}

// Инициализация всплывающих подсказок
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всплывающих подсказок Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Анимация для элементов при прокрутке
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.animate-on-scroll');
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            if (elementPosition < windowHeight - 50) {
                element.classList.add('fade-in');
                element.classList.remove('animate-on-scroll');
            }
        });
    };

    // Запускаем анимацию при загрузке и при прокрутке
    animateOnScroll();
    window.addEventListener('scroll', animateOnScroll);

    // Обработчик для формы обратной связи на главной странице
    const contactForm = document.querySelector('form');
    if (contactForm) {
        contactForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            const name = this.querySelector('#name').value;
            const email = this.querySelector('#email').value;
            const message = this.querySelector('#message').value;
            
            try {
                await sendData('/api/contact', 'POST', { name, email, message });
                showMessage('Спасибо! Ваше сообщение успешно отправлено.', 'success');
                this.reset();
            } catch (error) {
                showMessage('Не удалось отправить сообщение. Пожалуйста, попробуйте позже.', 'danger');
            }
        });
    }
}); 