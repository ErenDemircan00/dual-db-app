const token = localStorage.getItem('token'); // Token'ı al

        if (token) {
            document.getElementById('productForm').addEventListener('submit', function(event) {
                event.preventDefault();

                const name = document.getElementById('productName').value;
                const price = parseFloat(document.getElementById('productPrice').value);
                const description = document.getElementById('productDescription').value;

                fetch('/add-product', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': token  // Token'ı header'a ekliyoruz
                    },
                    body: JSON.stringify({ product_name: name, product_price: price, product_description: description })
                })
                .then(response => response.json())
                .then(data => {
                    alert('Product added!');
                })
                .catch(error => {
                    console.error('Error adding product:', error);
                    alert('Error adding product');
                });
            });
        }