<?php
// Test fixture for a disposable WooCommerce CI site only.
if ( ! class_exists( 'WC_Product_Simple' ) ) {
    WP_CLI::error( 'WooCommerce is not active.' );
}
$product = new WC_Product_Simple();
$product->set_name( 'CI Test Product' );
$product->set_regular_price( '12.50' );
// Avoid carrier/shipping integrations in the isolated offline checkout fixture.
$product->set_virtual( true );
$product->set_status( 'publish' );
$product->set_manage_stock( true );
$product->set_stock_quantity( 7 );
$id = $product->save();
if ( ! $id ) {
    WP_CLI::error( 'Failed to create CI product.' );
}
WP_CLI::success( 'Created test product ' . $id );
