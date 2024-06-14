######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
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
######################################################################

# spell: ignore Rofrano jsonify restx dbname
"""
Product Store Service with UI
"""
import logging

from flask import url_for  # noqa: F401 pylint: disable=unused-import
from flask import abort, jsonify, request

from service.common import status  # HTTP Status Codes
from service.models import Category, Product

from . import app


######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# C R E A T E   A   N E W   P R O D U C T
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    message = product.serialize()

    location_url = url_for("get_products", product_id=product.id, _external=True)
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# L I S T   A L L   P R O D U C T S
######################################################################
@app.route("/products", methods=["GET"])
def list_products():
    """
   gets all products
    """
    name = request.args.get('name')
    cat = request.args.get('category')
    avail = request.args.get('available')

    if name is not None:
        prods = Product.find_by_name(name)
    elif cat is not None:
        try:
            category = getattr(Category, str(cat).upper())
        except AttributeError as err:
            logging.error(err)
            return "", status.HTTP_400_BAD_REQUEST

        prods = Product.find_by_category(category)
    elif avail is not None:
        prods = Product.find_by_availability(
            avail in ['true', 'True', 'TRUE']
        )
    else:
        prods = Product.all()

    return jsonify([prod.serialize() for prod in prods]), status.HTTP_200_OK

######################################################################
# R E A D   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=["GET"])
def get_products(product_id: int):
    """
   gets one product
    """

    prod = Product.find(product_id)
    if prod is None:
        return "", status.HTTP_404_NOT_FOUND

    return jsonify(prod.serialize()), status.HTTP_200_OK

######################################################################
# U P D A T E   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id: int):
    """
   updates one product
    """
    app.logger.info("Request to update a Product...")
    check_content_type("application/json")

    if Product.find(product_id) is None:
        return "", status.HTTP_404_NOT_FOUND

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)

    product.id = product_id
    product.update()

    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# D E L E T E   A   P R O D U C T
######################################################################

@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_products(product_id: int):
    """
   deletes one product
    """

    prod = Product.find(product_id)
    if prod is None:
        return "", status.HTTP_404_NOT_FOUND

    prod.delete()
    return "", status.HTTP_204_NO_CONTENT
