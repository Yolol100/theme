<?php
/**
 * ACF fixtures for the disposable Docker site. Not part of the theme.
 * Run through WP-CLI: wp eval-file /workspace/acf_smoke.php seed|verify|revise|cleanup.
 */
if ( ! defined( 'WP_CLI' ) || ! WP_CLI || 'http://localhost:8080' !== get_option( 'home' ) ) {
    throw new RuntimeException( 'ACF fixtures may only run on the local CI site.' );
}

function starter_ci_require( $condition, $message ) {
    if ( ! $condition ) {
        WP_CLI::error( $message );
    }
}

$phase = $args[0] ?? '';
starter_ci_require( in_array( $phase, array( 'seed', 'verify', 'revise', 'cleanup' ), true ), 'Unknown ACF test phase.' );
starter_ci_require( function_exists( 'acf_update_field_group' ) && function_exists( 'get_field' ), 'ACF is not active.' );
starter_ci_require( defined( 'ACF_VERSION' ) && '6.8.10' === ACF_VERSION, 'Unexpected ACF version.' );
$state = get_option( 'starter_ci_acf_state', false );

if ( 'seed' === $phase ) {
    starter_ci_require( false === $state, 'An ACF fixture already exists; use a fresh CI database.' );
    starter_ci_require( 'webactueel-starter' === get_stylesheet(), 'The tested starter theme is not active.' );
    $markup = '<!-- wp:paragraph {"metadata":{"bindings":{"content":{"source":"acf/field","args":{"key":"starter_ci_summary"}}}}} --><p>CI fallback summary</p><!-- /wp:paragraph -->';
    $markup .= '<!-- wp:paragraph {"metadata":{"bindings":{"content":{"source":"acf/field","args":{"key":"starter_ci_internal"}}}}} --><p>CI hidden fallback</p><!-- /wp:paragraph -->';
    $pages = array();
    foreach ( array( 'alpha', 'beta', 'empty' ) as $name ) {
        $id = wp_insert_post( array(
            'post_type' => 'page', 'post_status' => 'publish',
            'post_title' => 'CI ACF ' . ucfirst( $name ),
            'post_name' => 'ci-acf-' . $name, 'post_content' => $markup,
        ), true );
        starter_ci_require( ! is_wp_error( $id ) && $id > 0, 'Could not create ACF fixture page.' );
        $pages[ $name ] = $id;
    }
    // Store the schema in the database, as the ACF field-group editor does.
    $group = acf_update_field_group( array(
        'key' => 'group_starter_ci_pages', 'title' => 'CI page fields', 'active' => true,
        'show_in_rest' => 0,
        'location' => array( array( array( 'param' => 'post_type', 'operator' => '==', 'value' => 'page' ) ) ),
    ) );
    starter_ci_require( ! empty( $group['ID'] ), 'ACF field group was not saved.' );
    foreach ( array( 'summary' => 1, 'internal' => 0 ) as $name => $allowed ) {
        $field = acf_update_field( array(
            'key' => 'field_starter_ci_' . $name, 'name' => 'starter_ci_' . $name,
            'label' => 'CI ' . $name, 'type' => 'text', 'parent' => $group['ID'],
            'allow_in_bindings' => $allowed,
        ) );
        starter_ci_require( ! empty( $field['ID'] ), 'ACF field was not saved.' );
    }
    $page_group = acf_update_field_group( array(
        'key' => 'group_starter_ci_alpha', 'title' => 'CI first-page fields', 'active' => true,
        'show_in_rest' => 0,
        'location' => array( array( array( 'param' => 'page', 'operator' => '==', 'value' => (string) $pages['alpha'] ) ) ),
    ) );
    starter_ci_require( ! empty( $page_group['ID'] ), 'Page-specific field group was not saved.' );
    $field = acf_update_field( array(
        'key' => 'field_starter_ci_detail', 'name' => 'starter_ci_detail',
        'label' => 'CI first-page detail', 'type' => 'text', 'parent' => $page_group['ID'],
        'allow_in_bindings' => 0,
    ) );
    starter_ci_require( ! empty( $field['ID'] ), 'Page-specific field was not saved.' );
    $values = array( 'alpha' => 'CI ACF Alpha value', 'beta' => 'CI ACF Beta value' );
    foreach ( $values as $name => $value ) {
        update_field( 'field_starter_ci_summary', $value, $pages[ $name ] );
        update_field( 'field_starter_ci_internal', 'CI restricted value must not render', $pages[ $name ] );
    }
    update_field( 'field_starter_ci_detail', 'Only the first page', $pages['alpha'] );
    $state = array( 'pages' => $pages, 'values' => $values, 'groups' => array( $group['ID'], $page_group['ID'] ) );
    update_option( 'starter_ci_acf_state', $state, false );
}

starter_ci_require( is_array( $state ) && isset( $state['pages'], $state['values'], $state['groups'] ), 'ACF fixture state is missing.' );
if ( 'revise' === $phase ) {
    $state['values']['alpha'] = 'CI ACF Alpha revised';
    update_field( 'field_starter_ci_summary', $state['values']['alpha'], $state['pages']['alpha'] );
    update_option( 'starter_ci_acf_state', $state, false );
}
if ( 'cleanup' === $phase ) {
    foreach ( $state['pages'] as $id ) {
        wp_delete_post( $id, true );
        starter_ci_require( null === get_post( $id ), 'ACF fixture page was not removed.' );
    }
    foreach ( $state['groups'] as $id ) {
        acf_delete_field_group( $id );
        starter_ci_require( null === get_post( $id ), 'ACF fixture group was not removed.' );
    }
    delete_option( 'starter_ci_acf_state' );
    starter_ci_require( false === get_option( 'starter_ci_acf_state', false ), 'ACF fixture state was not removed.' );
    WP_CLI::success( 'Removed ACF test data.' );
    return;
}

foreach ( $state['values'] as $name => $value ) {
    starter_ci_require( get_field( 'starter_ci_summary', $state['pages'][ $name ] ) === $value, 'ACF value changed or leaked between pages.' );
}
$alpha_groups = wp_list_pluck( acf_get_field_groups( array( 'post_id' => $state['pages']['alpha'], 'post_type' => 'page' ) ), 'key' );
$beta_groups = wp_list_pluck( acf_get_field_groups( array( 'post_id' => $state['pages']['beta'], 'post_type' => 'page' ) ), 'key' );
starter_ci_require( in_array( 'group_starter_ci_alpha', $alpha_groups, true ), 'First-page location rule did not match.' );
starter_ci_require( ! in_array( 'group_starter_ci_alpha', $beta_groups, true ), 'First-page field group leaked onto the second page.' );
starter_ci_require( 'Only the first page' === get_field( 'starter_ci_detail', $state['pages']['alpha'] ), 'Page-specific field value is missing.' );
starter_ci_require( ! get_field( 'starter_ci_detail', $state['pages']['beta'] ), 'Page-specific data leaked.' );
WP_CLI::line( wp_json_encode( array(
    'wordpress_version' => get_bloginfo( 'version' ), 'php_version' => PHP_VERSION,
    'acf_version' => ACF_VERSION, 'pages' => $state['pages'], 'values' => $state['values'],
) ) );
