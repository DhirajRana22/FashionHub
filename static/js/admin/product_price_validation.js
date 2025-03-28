document.addEventListener('DOMContentLoaded', function() {
    const priceInput = document.getElementById('id_price');
    if (priceInput) {
        priceInput.setAttribute('min', '0');
        priceInput.setAttribute('step', '0.01');
        
        priceInput.addEventListener('input', function(e) {
            const value = parseFloat(e.target.value);
            if (value < 0) {
                e.target.value = '0';
            }
        });

        // Prevent form submission if price is negative
        const form = priceInput.closest('form');
        form.addEventListener('submit', function(e) {
            const value = parseFloat(priceInput.value);
            if (value < 0) {
                e.preventDefault();
                alert('Price cannot be negative.');
                priceInput.value = '0';
                priceInput.focus();
            }
        });
    }
}); 