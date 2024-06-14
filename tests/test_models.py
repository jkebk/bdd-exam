# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should read a product"""
        product = ProductFactory()
        logging.debug("creating product %s")
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        actual = Product.find(product.id)
        self.assertDictEqual(product.serialize(), actual.serialize())

    def test_deserialize_errors(self):
        """it should check validation errors are raised"""
        with self.assertRaises(DataValidationError):
            ProductFactory().deserialize({})

        with self.assertRaises(DataValidationError):
            product = ProductFactory().serialize()
            product["category"] = "foo"

            ProductFactory().deserialize(product)

        with self.assertRaises(DataValidationError):
            product = ProductFactory().serialize()
            product["category"] = 1

            ProductFactory().deserialize(product)

    def test_update_a_product(self):
        """It should update a product"""
        product = ProductFactory()
        orig_desc = product.description
        logging.debug("creating product %s", product)
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        orig_id = product.id
        logging.debug("created product %s")

        new_desc = "an operating system"
        product.description = new_desc
        product.update()
        logging.debug("updated product %s")

        self.assertEqual(product.description, new_desc)
        self.assertEqual(product.id, orig_id)

        all_prods = Product.all()
        self.assertEqual(1, len(all_prods))
        self.assertEqual(orig_id, all_prods[0].id)
        self.assertNotEqual(orig_desc, all_prods[0].description)

    def test_update_without_id(self):
        """it should raise an error when no id is provided to update"""
        product = ProductFactory()
        product.id = None
        with self.assertRaises(DataValidationError):
            product.update()

    def test_delete_a_product(self):
        """It should delete a product"""
        product = ProductFactory()
        logging.debug("creating product %s", product)
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        self.assertEqual(1, len(Product.all()))

        Product.delete(product)
        self.assertEqual(0, len(Product.all()))

    def test_list_products(self):
        """It should list products"""

        self.assertEqual(0, len(Product.all()))
        count = 5
        products = [prod() for prod in [ProductFactory]*count]
        logging.debug("creating products %s", products)
        for prod in products:
            prod.id = None
            prod.create()
            self.assertIsNotNone(prod.id)

        self.assertEqual(5, len(Product.all()))

    def test_find_products_by_name(self):
        """it should find products by name"""

        self.assertEqual(0, len(Product.all()))
        count = 5
        products = [product() for product in [ProductFactory]*count]
        logging.debug("creating products %s", products)
        for product in products:
            product.id = None
            product.create()
            self.assertIsNotNone(product.id)

        first_name = products[0].name
        count = len(list(filter(lambda prod: prod.name == first_name, products)))

        found = Product.find_by_name(first_name)
        self.assertEqual(count, found.count())

        for result in found:
            self.assertEqual(first_name, result.name)

    def test_find_products_by_avail(self):
        """it should find products by availability"""

        self.assertEqual(0, len(Product.all()))
        count = 10
        products = [prod() for prod in [ProductFactory]*count]
        logging.debug("creating products %s", products)
        for product in products:
            product.id = None
            product.create()
            self.assertIsNotNone(product.id)

        avail = products[0].available
        count = len(list(filter(lambda p: p.available == avail, products)))

        found = Product.find_by_availability(avail)
        self.assertEqual(count, found.count())

        for result in found:
            self.assertEqual(avail, result.available)

    def test_find_products_by_cat(self):
        """it should find products by category"""

        self.assertEqual(0, len(Product.all()))
        count = 10
        products = [prod() for prod in [ProductFactory]*count]
        logging.debug("creating products %s", products)
        for product in products:
            product.id = None
            product.create()
            self.assertIsNotNone(product.id)

        cat = products[0].category
        count = len(list(filter(lambda p: p.category == cat, products)))

        found = Product.find_by_category(cat)
        self.assertEqual(count, found.count())

        for result in found:
            self.assertEqual(cat, result.category)

    def test_find_products_by_price(self):
        """it should find products by price"""

        self.assertEqual(0, len(Product.all()))
        count = 10
        products = [prod() for prod in [ProductFactory]*count]
        logging.debug("creating products %s", products)
        for product in products:
            product.id = None
            product.create()
            self.assertIsNotNone(product.id)

        price = products[0].price
        count = len(list(filter(lambda product: product.price == price, products)))

        found = Product.find_by_price(price)
        self.assertEqual(count, found.count())

        for result in found:
            self.assertEqual(price, result.price)

        # using string
        found = Product.find_by_price(f'"{price}"')
        self.assertEqual(count, found.count())

        for result in found:
            self.assertEqual(price, result.price)
