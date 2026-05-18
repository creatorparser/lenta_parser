import random
import string


def generate_sessiontoken():
    """
    Генерирует случайный sessiontoken.
    
    Returns:
        str: Случайный sessiontoken (18 символов в верхнем регистре)
    """
    chars = string.digits + string.ascii_uppercase
    return ''.join(random.choice(chars) for _ in range(18))


def product_headers(spider, sessiontoken=None):
    """
    Генерирует заголовки для запросов к API Lenta.
    
    Args:
        spider: Экземпляр паука, наследуемого от CrawlerSpider
        sessiontoken: Опциональный sessiontoken для использования
    
    Returns:
        dict: Словарь заголовков со случайным user-agent
    """
    # Если sessiontoken не передан, генерируем новый
    if sessiontoken is None:
        sessiontoken = generate_sessiontoken()
    headers = {
        'accept': 'application/json',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'no-cache',
        'client': 'angular_web_0.0.2',
        'content-type': 'application/json',
        'deviceid': '075b7e93-5a0a-19fa-0192-457d25186075',
        'experiments': 'exp_recommendation_cms.true, exp_lentapay.test, exp_profile_bell.test, exp_cl_omni_authorization.test, exp_fullscreen.test, exp_onboarding_editing_order.test, exp_cart_new_carousel.default, exp_sbp_enabled.default, exp_profile_settings_email.default, exp_cl_omni_refusalprintreceipts.test, exp_search_suggestions_popular_sku.default, exp_cl_new_csi.test, exp_cl_new_csat.default, exp_delivery_price_info.test, exp_interval_jump.test, exp_cardOne_promo_type.test, exp_birthday_coupon_skus.test, exp_qr_cnc.test, exp_where_place_cnc.test, exp_editing_cnc_onboarding.test, exp_editing_cnc.test, exp_pickup_in_delivery.test, exp_welcome_onboarding.default, exp_where_place_new.default, exp_start_page.default, exp_default_payment_type.default, exp_start_page_onboarding.default, exp_search_new_logic.default, exp_referral_program_type.default, exp_new_action_pages.default, exp_items_by_rating.test, exp_can_accept_early.default, exp_online_subscription.default, exp_hide_cash_payment_for_cnc_wo_adult_items.default, exp_prices_per_quantum.test, exp_web_chips_online.test, exp_promo_without_benefit.default, exp_cart_forceFillDelivery.default, exp_banner_sbp_checkout_step_3.control, exp_badge_sbp_checkout_step_3.test_B, exp_kit_banner_sbp_checkout_step_3.default, exp_kit_badge_sbp_checkout_step_3.default, exp_profile_stories.test, exp_cl_new_ui_csi_comment.default, exp_in_app_update.default, exp_sorting_catalog.default, exp_aa_test_2025_04.control, exp_search_items_by_date.test_B, exp_product_page_by_blocks.default, exp_without_a_doorbell.test_A, exp_without_a_doorbell_new.default, exp_edit_payment_type.test, exp_edit_payment_type_new.default, exp_search_photo_positions.default, exp_new_matrix.test, exp_another_button_ch.default, exp_progressbar_and_title.test, exp_auto_fill_coupon.default, exp_promo_and_bonus.test, exp_about_cnc_optimization.default, exp_online_categories.default, exp_no_intervals.default, exp_web_b2b_excel_load.default, exp_cart_save_with_promo.default, exp_email_optional_full_registration.default, exp_new_navigation_web.test, exp_cl_new_rateapp.default, exp_similar_goods_cart.test, exp_cart_redesign_promocode.default, exp_search_new_filters.test, exp_loyalty_categories_labels.default, exp_search_multicard.test, exp_delivery_promocode_bd_coupon.default, exp_search_disable_fuzziness.default, exp_ui_catalog_level_2.default, exp_fullscreen_inapp_vs_native.test1, exp_search_collections_ranking.test, exp_search_elastic_tokens.default, exp_cl_new_tapbar.default, exp_cl_new_tapbar_tab.default, exp_search_my_choice_stock_priority.test_b, exp_cart_free_sample.default, exp_about_promocode.test_A, exp_personal_promo_detail_for_delivery.test_2, exp_search_combined_field.default, exp_search_unified.default, exp_web_personal_promo_detail_for_delivery.default, exp_web_personal_promo_delivery_chips.test, exp_b2b_web_mob_checkout.default, exp_personal_promo_delivery_chips.default, exp_ds_cnc_pers_recom.test, exp_ds_mntk_pers_recom.default, exp_shopping_statistics.default, exp_pin_create_button.default, exp_search_ui_catalog_pim.default, exp_search_video.default, exp_search_pinned_reviews.test, exp_sbp_instead_of_lenta_pay.default, exp_card1_start_page.default, exp_new_navigation_web_search.test, exp_new_navigation_web_actions.test, exp_status_assemble_completed.test, exp_cl_new_ui_csi_comment2.default, exp_online_subscription_discount.test, exp_start_page_button_notifications.default, exp_quick_checkout.default, exp_quick_checkout_update.default, exp_new_goods_widget_processing.default, exp_search_no_stock.true, exp_brief_description_promo.default, exp_new_offer_new_user_v1.default, exp_order_feedback_show.default, exp_leave_order_at_door.test, exp_leave_order_at_door_new.test, exp_search_quantity_discount_promo.test, exp_start_page_button_navigation_off.default, exp_obi_webview.true, exp_huawei_adjust_new_tokens.true, exp_import_goods_in_basket.default, exp_unpin_tabbar.default, exp_mna_orders_editing.default, exp_consent.default, exp_main_stories.test, exp_from_store_myself.default, exp_new_bs_catalog_startpage.default, exp_be_soon_show_explain_message.default, exp_startpage_mainpage_new_address_design.default, exp_bubble_discount_startpage_mainpage.test, exp_startpage_zone_description.default, exp_ds_pd_carousel.default, exp_ds_pers_recom_delivery_2.test, exp_search_ds_catboost_2.control, exp_novikov_test.OFF, exp_order_created_action_banner.default, exp_ds_mntk_pers_cat.default, exp_search_ds_empty_recom.default, exp_badges_pers_cashback.default, exp_temp_exp_ds_pd_carousel_android.default, exp_temp_exp_ds_pd_carousel_android_general.default, exp_temp_samesplit_check_f.default, exp_interval_jump_30.default, exp_temp_exp_ds_pd_carousel_ios_general.default, exp_search_purchased_badge.default, exp_pwa_cart.default, exp_pwa_checkout.default, exp_auto_detection_store_for_new_user.default, exp_return_available_items.default, exp_b2c_onboarding_send_cart.test, exp_b2b_send_cart.default, exp_b2c_send_cart.test, exp_cart_item_modify_version20.default, exp_auth_sber_id.default, exp_search_voice_search_ai.default, exp_startpage_redesign_qr_and_loy.default, exp_web_aa_2026_01_v1.test, exp_startpage_redesign_missions.default, exp_search_pdp_big_photo.default, exp_startpage_tab_shop_on_the_map.default, exp_startpage_logics_button_pickup.default, exp_open_screen_card1_profile_without_address.default, exp_web_cancel_to_edit_cnc.test, exp_ch_how_much_unit.test, exp_search_fd.default, exp_authorization_tg.default, exp_ds_cat_diversity.test, exp_more_about_price.default, exp_br_1521_refresh_auth_token.default, exp_kpp_aa.default, exp_unpin_tabbar_v2.default, exp_b2c_bot_web_send_cart.default, exp_nearest_hubs_new_logic.default, exp_new_bs_catalog_startpage_v2.default, exp_favorite_categories_description.default, exp_start_page_mobweb.default, exp_test_toggle_b2b_b2c_web.test, exp_startpage_free_delivery.default, exp_search_custom_qty.default, exp_allow_push_notifications.default, exp_time_track.default, exp_auth_call.default, exp_search_ds_bandit_3.default, exp_web_pickup_popup_map_2192.default, exp_new_counter_web.test, exp_ds_main_page_goods_waterfall.default, exp_startpage_hovering_basket_gr_2272.default, exp_yandex_pay_available.default, exp_pwa_vertical_pers_recom.default, exp_search_pdp_banner.default, exp_ds_main_page_web_goods_waterfall.default, exp_search_price_filter.default, exp_qr_code_action_banner.default, exp_gr_2584_auth_vk_id_yandex_id.default, exp_disable_delivery_price_info.default, exp_swap_empty_delivery_info.test_B, exp_swap_min_delivery_info.test_B, exp_authorization_vpn.test, exp_search_pdp_new_badges.default, exp_status_on_main.default, exp_status_on_landing.default, exp_time_in_minutes_gr_2527.default, exp_delivery_after_promocode.test, exp_offer_different_discounts.default, exp_b2b_profile_hide_sidebar.default, exp_edit_promocode.default, exp_web_cancel_to_promoedit.default, exp_main_page_new_mode_shop_v2.default, exp_cheap_no_intervals.default, exp_cart_photo_badge_packaging.default, exp_two_intervals.default, exp_cl_new_csat_comment.default, exp_cart_title_mode.default, exp_web_card_favoriteCategoriesWidget.control, exp_search_ds_bandit_4.default, exp_ch22405cartwithoutmonolith.test, exp_reason_for_cancellation.default, exp_search_new_plp.default, exp_pwa_profile.default, exp_fetch_deprecated_toggles_from_cdn.default, exp_main_page_new_button_shop_v2.default, exp_main_page_pers_offer_app.default, exp_main_page_pers_offer_web.control, exp_main_page_new_mode_content.default, exp_start_page_new_widgets_cms.default, exp_search_skip_catalog_level_2.default, exp_web_default_address.test, exp_redesign_address_search_and_map.default, exp_b2b_itemization_of_beer.test, exp_b2b_web_mercurian_products_checkbox_ux.default, exp_b2b_web_mobile_payments_redesign.default, exp_b2b_web_document_templates_hub.true, exp_b2b_web_referral_banner.true, exp_b2b_onboarding_send_cart.test',
        'origin': 'https://lenta.com',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://lenta.com',
        'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sessiontoken': sessiontoken,
        'user-agent': spider.get_random_user_agent(),
        'x-delivery-mode': 'pickup',
        'x-device-brand': '',
        'x-device-name': '',
        'x-device-os': 'Web',
        'x-device-os-version': '12.4.8',
        'x-device-web-platform': 'desktop_web',
        'x-domain': 'moscow',
        'x-organization-id': '',
        'x-platform': 'omniweb',
        'x-retail-brand': 'lo',
    }
    return headers
