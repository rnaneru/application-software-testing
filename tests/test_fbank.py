import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "http://localhost:8000/"
RUB_CARD_NUMBER = "1234 5678 9012 3456"
INVALID_CARD_NUMBER_17 = "1111 1111 1111 1111 1"

class TestFBank:

    def select_rub_account(self, driver):
        rub_card = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//h2[text()='Рубли']/ancestor::div[@role='button' and contains(@class, 'g-card_type_action')]"))
        )
        rub_card.click()
        driver.implicitly_wait(1)

    def enter_card_number(self, driver, card_number):
        card_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='0000 0000 0000 0000']"))
        )
        card_input.clear()
        for digit in card_number:
            card_input.send_keys(digit)
            driver.implicitly_wait(0.05)
        return card_input

    def enter_amount(self, driver, amount):
        amount_input = driver.find_element(By.XPATH, "//input[@placeholder='1000' and preceding-sibling::h3[text()='Сумма перевода:']]")
        amount_input.clear()
        amount_input.send_keys(str(amount))
        return amount_input

    def click_transfer_button(self, driver):
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Перевести']]"))
        )
        button.click()

    @pytest.mark.parametrize("invalid_amount", [0, -10, ""])
    def test_transfer_with_invalid_amount(self, driver, invalid_amount):
        """Перевод с невалидной суммой (0, -10, пустая строка) должен быть заблокирован."""
        driver.get(URL)
        self.select_rub_account(driver)
        self.enter_card_number(driver, RUB_CARD_NUMBER)
        self.enter_amount(driver, invalid_amount)
        self.click_transfer_button(driver)

        with pytest.raises(Exception):
            alert = driver.switch_to.alert
            alert_text = alert.text
            assert "принят банком" not in alert_text
            alert.dismiss()

    def test_amount_field_appears_with_invalid_card_length(self, driver):
        """Поле 'Сумма перевода' не должно появляться при номере карты из 17 цифр."""
        driver.get(URL)
        self.select_rub_account(driver)
        self.enter_card_number(driver, INVALID_CARD_NUMBER_17)

        amount_inputs = driver.find_elements(By.XPATH, "//input[@placeholder='1000' and preceding-sibling::h3[text()='Сумма перевода:']]")
        assert len(amount_inputs) == 0, "Поле суммы появилось при невалидной длине карты"

    @pytest.mark.parametrize("amount, expected_fee", [(99, 9), (50, 5), (1, 0)])
    def test_commission_calculation_for_small_amounts(self, driver, amount, expected_fee):
        """Расчёт комиссии для сумм менее 100 единиц."""
        driver.get(URL)
        self.select_rub_account(driver)
        self.enter_card_number(driver, RUB_CARD_NUMBER)
        self.enter_amount(driver, amount)

        commission_span = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "comission"))
        )
        actual_fee = int(commission_span.text)
        assert actual_fee == expected_fee, f"Для суммы {amount} ожидалась комиссия {expected_fee}, получено {actual_fee}"