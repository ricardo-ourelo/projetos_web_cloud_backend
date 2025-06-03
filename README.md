
#  API – Projeto Backend

REST API para gestão de utilizadores, autenticação, produtos e carrinhos de compra.

Base URL:


http://localhost:5000


A maioria dos endpoints protegidos requerem token de autenticação JWT via query param:


?token=TOKEN




##  Autenticação

### Login

* Método: POST
* URL: /user/login
* Descrição: Realiza login e retorna um token JWT.

Corpo:

```json
{
  "username": "Maria",
  "password": "pass123"
}
```

---

## Gestão de Utilizadores

### Registar Utilizador

* Método: POST
* URL: /user/register
* Descrição: Regista um novo utilizador com role "user".

Corpo:

```json
{
  "username": "Jorge",
  "password": "Jorge123",
  "role": "user"
}
```

### Registar Administrador

* Método: POST
* URL: /user/register
* Descrição: Regista um utilizador com role "admin".

Corpo:

```json
{
  "username": "admin",
  "password": "admin123",
  "role": "admin"
}
```

### Confirmar Utilizador

* Método: POST
* URL: /user/confirmation?token=ADMIN_TOKEN
* Descrição: Admin confirma o registo de um utilizador.

Corpo:

```json
{
  "username": "Jorge"
}
```


## Produtos

### Listar Produtos

* Método: GET
* URL: /products
* Descrição: Retorna todos os produtos com paginação.

Parâmetros (query):

* page (opcional)
* per_page (opcional)


### Ver Produto por ID

* Método: GET
* URL: /products/{id}
* Exemplo: /products/6825b2c156e7d99fb41ef13a
* Descrição: Retorna produto específico através do ID


### Adicionar Produto

* Método: POST
* URL: /products?token=ADMIN_TOKEN
* Descrição: Adiciona um novo produto (requer token).

Exemplo:

```json
{
  "category": "camisas",
  "description": "Isto é um produto adicionado manualmente",
  "gender": "homem",
  "id": 511,
  "image": "/assets/images/products/CamisaH3 - 1.jpg",
  "images": [
    "/assets/images/products/CamisaH3 - 1.jpg",
    "/assets/images/products/CamisaH3 - 2.jpg",
    "/assets/images/products/CamisaH3 - 3.jpg"
  ],
  "name": "Camisa 100% linho bege",
  "popularity": 70,
  "price": 12.99,
  "rating": 4.7,
  "stock": 16,
  "subcategory": "",
  "variants": [
    { "color": "Bege", "size": "S", "stock": 4 },
    { "color": "Bege", "size": "M", "stock": 4 },
    { "color": "Bege", "size": "L", "stock": 4 },
    { "color": "Bege", "size": "XL", "stock": 4 }
  ]
}
```



### Atualizar Produto

* Método: PUT
* URL: /products/{id}?token=ADMIN_TOKEN
* Exemplo: /products/683dacf62cc4662b36aade19
* Descrição: Altera campos do produto

Corpo:

```json
{
  "description": "Uma descrição diferente"
}
```



### Remover Produto

* Método: DELETE
* URL: /products/{id}?token=ADMIN_TOKEN
* Exemplo: /products/683f3b63b865a97e6adae639
* Descrição: Remove o produto através do ID



### Produtos em Destaque

* Método: GET
* URL: /products/featured
* Descrição: Lista os produtos com mais destaque (por ordem de popularidade).



### Produtos por Categoria

* Método: GET
* URL: /products/categories/{categoria}?page=1&per_page=10
* Exemplo: /products/categories/camisas?page=1&per_page=10
* Descrição: Filtra produtos por categoria com paginação



### Produtos por Preço

* Método: GET
* URL: /products/price
* Parâmetros esperados (query):

  * min
  * max
  * sort (asc ou desc)
  * page, per_page (opcional)



## Carrinho

### Guardar Carrinho

* Método: POST
* URL: /products/cart?token=TOKEN
* Descrição: Guarda produtos no carrinho de um utilizador autenticado.

Corpo:

```json
{
  "products": [
    { "product_id": "665a6be2c7d1a3a0e2cfc567", "quantity": 2 },
    { "product_id": "665a6be2c7d1a3a0e2cfc568", "quantity": 1 }
  ]
}
```

