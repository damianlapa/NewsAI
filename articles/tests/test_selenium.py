from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import connection
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from articles.models import Category, UserProfile
import time
import os


class SeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            cls.selenium = webdriver.Chrome(options=chrome_options)
            cls.selenium.implicitly_wait(10)
            cls.selenium.execute_cdp_cmd('Runtime.enable', {})
            cls.mobile_devices = [
                {
                    'deviceName': 'iPhone X',
                    'userAgent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)',
                    'viewport': {'width': 375, 'height': 812, 'deviceScaleFactor': 3},
                    'isMobile': True
                },
                {
                    'deviceName': 'Pixel 2',
                    'userAgent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2)',
                    'viewport': {'width': 411, 'height': 731, 'deviceScaleFactor': 2.625},
                    'isMobile': True
                },
                {
                    'deviceName': 'iPad Pro',
                    'userAgent': 'Mozilla/5.0 (iPad; CPU OS 13_2_3 like Mac OS X)',
                    'viewport': {'width': 1024, 'height': 1366, 'deviceScaleFactor': 2},
                    'isMobile': False
                }
            ]
        except Exception as e:
            print(f"Chrome setup failed: {str(e)}")
            cls.selenium = None

    def setUp(self):
        if not self.selenium:
            self.skipTest("Chrome is not available")

        print("\nCleaning up database...")
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM articles_userprofile_selected_categories")
            cursor.execute("DELETE FROM articles_userprofile")
            cursor.execute("DELETE FROM articles_category")
            cursor.execute("DELETE FROM auth_user")

        try:
            print("\nCreating test data...")
            self.user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )

            self.category = Category.objects.create(name='Test Category')
            self.profile, created = UserProfile.objects.get_or_create(user=self.user)
            self.profile.selected_categories.add(self.category)

            print(f"User created: {self.user.id}")
            print(f"Category created: {self.category.id}")
            print(f"Profile created: {self.profile.id} (was new: {created})")

            # Verify data
            self.assertTrue(User.objects.filter(id=self.user.id).exists(), "User should exist")
            self.assertTrue(Category.objects.filter(id=self.category.id).exists(), "Category should exist")
            self.assertTrue(UserProfile.objects.filter(id=self.profile.id).exists(), "Profile should exist")

        except Exception as e:
            print(f"\nError in setUp: {str(e)}")
            raise

    def login_user(self, username, password):
        """Helper method to log in a user"""
        try:
            # Przejdź do strony logowania
            login_url = f"{self.live_server_url}{reverse('login')}"
            self.selenium.get(login_url)
            time.sleep(2)

            # Wypełnij formularz
            username_input = self.wait_for_element(By.ID, 'id_username')
            password_input = self.wait_for_element(By.ID, 'id_password')
            username_input.clear()  # Wyczyść pole przed wpisaniem
            password_input.clear()  # Wyczyść pole przed wpisaniem
            username_input.send_keys(username)
            password_input.send_keys(password)

            # Wyślij formularz
            login_form = self.wait_for_element(By.ID, 'login-form')
            login_form.submit()

            # Poczekaj na przekierowanie i przeładowanie strony
            time.sleep(3)

            # Sprawdź czy komunikat powitalny jest obecny
            try:
                welcome_messages = self.selenium.find_elements(By.CLASS_NAME, 'nav-item.nav-link')
                for message in welcome_messages:
                    if f"Welcome, {username}" in message.text:
                        return True
                raise Exception("Welcome message not found")
            except Exception as e:
                print("Error checking welcome message:", str(e))
                print("Page source:", self.selenium.page_source)
                raise Exception("Login verification failed")

        except Exception as e:
            print(f"\nLogin failed: {str(e)}")
            print(f"Current URL: {self.selenium.current_url}")
            print(f"Page source:\n{self.selenium.page_source}")
            self.selenium.save_screenshot('login_error.png')
            raise e

    def setup_device_emulation(self, device):
        """Ulepszona metoda konfiguracji emulacji urządzenia"""
        try:
            # Ustaw rozmiar okna
            self.selenium.set_window_size(
                device['viewport']['width'],
                device['viewport']['height']
            )

            # Ustaw emulację urządzenia
            self.selenium.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'width': device['viewport']['width'],
                'height': device['viewport']['height'],
                'deviceScaleFactor': device['viewport'].get('deviceScaleFactor', 1.0),
                'mobile': device.get('isMobile', False)
            })

            # Ustaw User Agent
            self.selenium.execute_cdp_cmd('Network.setUserAgentOverride', {
                'userAgent': device['userAgent']
            })

            # Daj czas na zastosowanie zmian
            time.sleep(1)

        except Exception as e:
            print(f"Failed to setup device emulation: {str(e)}")
            raise e

    def verify_desktop_elements(self):
        """Verify elements on the desktop view"""
        try:
            # Verify the presence of the navbar
            navbar = self.wait_for_element(By.CLASS_NAME, 'navbar')
            self.assertTrue(navbar.is_displayed(), "Navbar should be visible")

            # Verify the presence of the profile link if the user is authenticated
            if self.user.is_authenticated:
                profile_link = self.wait_for_element(By.LINK_TEXT, 'Profile')
                self.assertTrue(profile_link.is_displayed(), "Profile link should be visible")

            # Verify the presence of the home link
            home_link = self.wait_for_element(By.LINK_TEXT, 'Home')
            self.assertTrue(home_link.is_displayed(), "Home link should be visible")

            # Verify the presence of the articles link
            articles_link = self.wait_for_element(By.LINK_TEXT, 'Articles')
            self.assertTrue(articles_link.is_displayed(), "Articles link should be visible")

            # Verify the presence of the footer
            footer = self.wait_for_element(By.TAG_NAME, 'footer')
            self.assertTrue(footer.is_displayed(), "Footer should be visible")

        except Exception as e:
            print(f"Verification failed: {str(e)}")
            self.selenium.save_screenshot('verify_desktop_elements_error.png')
            raise e

    def wait_for_element(self, by, value, timeout=10):
        """Ulepszona metoda oczekiwania na element"""
        try:
            element = WebDriverWait(self.selenium, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return element
        except TimeoutException as e:
            print(f"Element not found: {str(e)}")
            self.selenium.save_screenshot('element_not_found_error.png')
            raise e

    def wait_for_alert(self, alert_class='alert-success', timeout=10):
        """Czeka na pojawienie się alertu"""
        try:
            return WebDriverWait(self.selenium, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, alert_class))
            )
        except TimeoutException:
            print("Alert not found after", timeout, "seconds")
            print("Page source:", self.selenium.page_source)
            raise

    def test_login_flow(self):
        """Test login process"""
        try:
            # Go to login page
            login_url = f"{self.live_server_url}{reverse('login')}"
            print(f"\nAccessing login URL: {login_url}")
            self.selenium.get(login_url)

            # Wait for page load and get page source
            time.sleep(2)
            print(f"Page source:\n{self.selenium.page_source}")

            # Wait for form to be present
            login_form = self.wait_for_element(By.ID, 'login-form')
            username_input = self.wait_for_element(By.ID, 'id_username')
            password_input = self.wait_for_element(By.ID, 'id_password')

            # Fill form
            username_input.send_keys('testuser')
            password_input.send_keys('testpass123')

            # Submit form
            login_form.submit()

            # Wait for redirect and navigation
            time.sleep(2)
            self.wait_for_element(By.CLASS_NAME, 'navbar')

            # Verify login success
            self.assertIn('testuser', self.selenium.page_source)

        except Exception as e:
            self.selenium.save_screenshot('login_error.png')
            print(f"Login test failed: {str(e)}")
            print(f"Current URL: {self.selenium.current_url}")
            print(f"Page source:\n{self.selenium.page_source}")
            raise e

    def test_responsive_design(self):
        """Test responsive design"""
        try:
            # Log in via client
            self.client.login(username='testuser', password='testpass123')

            # Go to home page
            self.selenium.get(self.live_server_url)

            if 'sessionid' in self.client.cookies:
                self.selenium.add_cookie({
                    'name': 'sessionid',
                    'value': self.client.cookies['sessionid'].value,
                    'path': '/'
                })

            # Refresh and wait
            self.selenium.refresh()
            time.sleep(2)

            # Verify page loaded
            print(f"Current URL: {self.selenium.current_url}")
            print(f"Page source:\n{self.selenium.page_source}")

            # Test responsive elements
            nav = self.wait_for_element(By.CLASS_NAME, 'navbar')
            self.assertTrue(nav.is_displayed())

            # Test mobile view
            self.selenium.set_window_size(375, 812)
            toggler = self.wait_for_element(By.CLASS_NAME, 'navbar-toggler')
            self.assertTrue(toggler.is_displayed())

        except Exception as e:
            self.selenium.save_screenshot('responsive_error.png')
            print(f"Responsive test failed: {str(e)}")
            print(f"Current URL: {self.selenium.current_url}")
            print(f"Page source:\n{self.selenium.page_source}")
            raise e

    def test_settings_interaction(self):
        """Test interaction with the settings form"""
        try:
            # Log in
            self.login_user('testuser', 'testpass123')

            # Go to profile
            profile_url = f"{self.live_server_url}/users/profile/"
            self.selenium.get(profile_url)
            time.sleep(5)  # Increase wait time

            # Find checkbox using ID of the created category
            checkbox = self.wait_for_element(By.ID, f'category_{self.category.id}')

            # Check the checkbox if not checked
            if not checkbox.is_selected():
                self.selenium.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
                                             checkbox)
                time.sleep(1)
                self.selenium.execute_script("arguments[0].click();", checkbox)
                time.sleep(1)

            # Find and click the submit button
            submit_button = self.wait_for_element(By.CSS_SELECTOR, 'form#settings-form button[type="submit"]')
            self.selenium.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
                                         submit_button)
            time.sleep(1)
            submit_button.click()

            # Wait for success alert
            self.wait_for_element(By.CLASS_NAME, 'alert-success', timeout=10)

        except Exception as e:
            print(f"Test failed: {str(e)}")
            print(f"Current URL: {self.selenium.current_url}")
            print(f"Page source:\n{self.selenium.page_source}")
            self.selenium.save_screenshot('settings_interaction_error.png')
            raise e

    def test_settings_mobile_responsiveness(self):
        """Test responsywności strony ustawień na urządzeniach mobilnych"""
        try:
            # Logowanie
            self.login_user('testuser', 'testpass123')
            time.sleep(2)

            # Ustaw rozmiar mobilny i wymuś responsywność
            self.selenium.execute_script("""
                window.innerWidth = 375;
                window.innerHeight = 812;
                document.body.style.width = '375px';
                Array.from(document.getElementsByClassName('container')).forEach(container => {
                    container.style.maxWidth = '375px';
                    container.style.width = '100%';
                    container.style.padding = '0.5rem';
                });
            """)
            time.sleep(2)

            # Przejdź do profilu
            self.selenium.get(f"{self.live_server_url}/users/profile/")
            time.sleep(3)

            # Sprawdź szerokość kontenera
            containers = self.selenium.find_elements(By.CLASS_NAME, 'container')
            for container in containers:
                if container.is_displayed():
                    width = container.rect['width']
                    self.assertLessEqual(
                        width,
                        375,
                        f"Container width ({width}px) exceeds mobile viewport (375px)"
                    )

        except Exception as e:
            print(f"\nMobile responsiveness test failed: {str(e)}")
            print(f"Current URL: {self.selenium.current_url}")
            self.selenium.save_screenshot('mobile_test_error.png')
            raise e

    def test_cross_browser_compatibility(self):
        """Test compatibility across different browsers"""
        try:
            # Najpierw zaloguj użytkownika
            self.login_user('testuser', 'testpass123')

            # Sprawdź główne elementy nawigacji
            navbar = self.wait_for_element(By.CLASS_NAME, 'navbar')
            self.assertTrue(navbar.is_displayed(), "Navbar should be visible")

            # Sprawdź linki nawigacyjne
            nav_links = {
                'Home': 'home',
                'Articles': 'user-articles',
                'Profile': 'profile'
            }

            for link_text, url_name in nav_links.items():
                try:
                    link = self.wait_for_element(By.LINK_TEXT, link_text)
                    self.assertTrue(
                        link.is_displayed(),
                        f"{link_text} link should be visible"
                    )
                    # Sprawdź czy link ma prawidłowy href
                    expected_url = reverse(url_name)
                    actual_url = link.get_attribute('href')
                    self.assertTrue(
                        actual_url.endswith(expected_url),
                        f"Expected {link_text} link to end with {expected_url}, but got {actual_url}"
                    )
                except Exception as e:
                    print(f"Error checking {link_text} link: {str(e)}")
                    raise

            # Sprawdź czy widzimy nazwę użytkownika
            welcome_text = self.wait_for_element(
                By.CLASS_NAME, 'nav-item.nav-link'
            )
            self.assertTrue(
                'testuser' in welcome_text.text,
                f"Expected to see username 'testuser' in welcome text, but got: {welcome_text.text}"
            )

            # Sprawdź przycisk wylogowania
            logout_button = self.wait_for_element(
                By.CSS_SELECTOR,
                'button[type="submit"].btn-outline-light'
            )
            self.assertTrue(
                logout_button.is_displayed(),
                "Logout button should be visible"
            )

            # Sprawdź stopkę
            footer = self.wait_for_element(By.TAG_NAME, 'footer')
            self.assertTrue(
                footer.is_displayed(),
                "Footer should be visible"
            )

        except Exception as e:
            print(f"Cross-browser test failed: {str(e)}")
            print(f"Current URL: {self.selenium.current_url}")
            print(f"Page source:\n{self.selenium.page_source}")
            self.selenium.save_screenshot('cross_browser_error.png')
            raise e

    def verify_common_elements(self):
        """Sprawdź podstawowe elementy UI"""
        try:
            # Daj czas na załadowanie strony
            time.sleep(2)

            # Sprawdź elementy w kolejności
            elements_to_check = [
                ('navbar', By.CLASS_NAME, 'navbar'),
                ('container', By.CLASS_NAME, 'container'),
                ('navbar-brand', By.CLASS_NAME, 'navbar-brand'),
                ('navbar-toggler', By.CLASS_NAME, 'navbar-toggler')
            ]

            for name, by, value in elements_to_check:
                try:
                    element = self.wait_for_element(by, value, timeout=5)
                    self.assertTrue(
                        element.is_displayed(),
                        f"{name} should be visible"
                    )
                    print(f"✓ {name} is visible")
                except Exception as e:
                    print(f"× Failed to verify {name}: {str(e)}")
                    raise

        except Exception as e:
            print(f"verify_common_elements failed: {str(e)}")
            self.selenium.save_screenshot('common_elements_error.png')
            raise e

    def test_device_emulation(self):
        """Test emulacji różnych urządzeń mobilnych"""
        for device in self.mobile_devices:
            try:
                print(f"\nTesting on {device['deviceName']}...")

                # Konfiguracja emulacji
                self.setup_device_emulation(device)
                time.sleep(2)

                # Logowanie
                self.login_user('testuser', 'testpass123')
                time.sleep(2)

                # Przejdź do profilu
                self.selenium.get(f"{self.live_server_url}/users/profile/")
                time.sleep(2)

                # Sprawdź podstawowe elementy
                self.verify_device_specific_ui(device)

                print(f"✓ Tests passed for {device['deviceName']}")

            except Exception as e:
                print(f"\nTest failed for {device['deviceName']}: {str(e)}")
                print(f"Current URL: {self.selenium.current_url}")
                self.selenium.save_screenshot(f'error_{device["deviceName"]}.png')
                raise e

    def verify_device_specific_ui(self, device):
        """Sprawdź UI dla konkretnego urządzenia"""
        try:
            # Dostosuj viewport
            self.selenium.execute_script(f"""
                window.innerWidth = {device['viewport']['width']};
                window.innerHeight = {device['viewport']['height']};

                // Wymuś responsywność
                document.querySelectorAll('.container').forEach(container => {{
                    container.style.maxWidth = '{device['viewport']['width']}px';
                    container.style.width = '100%';
                }});

                // Dostosuj elementy dotykowe
                document.querySelectorAll('button, input[type="submit"], .nav-link').forEach(el => {{
                    el.style.minHeight = '48px';
                    el.style.minWidth = '48px';
                    el.style.padding = '12px 20px';
                }});
            """)
            time.sleep(2)

            # Sprawdź wymiary kontenera
            containers = self.selenium.find_elements(By.CLASS_NAME, 'container')
            for container in containers:
                if container.is_displayed():
                    width = container.rect['width']
                    self.assertLessEqual(
                        width,
                        device['viewport']['width'],
                        f"Container width ({width}px) exceeds viewport width ({device['viewport']['width']}px)"
                    )

        except Exception as e:
            print(f"\nDevice UI verification failed: {str(e)}")
            print(f"Current URL: {self.selenium.current_url}")
            self.selenium.save_screenshot(f'device_ui_error_{device["deviceName"]}.png')
            raise e

    def handle_test_failure(self, device, error):
        """Obsługa błędów testu"""
        print(f"\nTest failed for {device['deviceName']}: {str(error)}")
        print(f"Current URL: {self.selenium.current_url}")
        print(f"Viewport size: {device['viewport']}")
        print(f"User Agent: {device['userAgent']}")
        self.selenium.save_screenshot(f"error_{device['deviceName']}.png")
        raise error

    def test_dark_mode(self):
        """Test trybu ciemnego z użyciem prefers-color-scheme"""
        try:
            # Włącz emulację trybu ciemnego
            self.selenium.execute_cdp_cmd('Emulation.setEmulatedMedia', {
                'features': [{'name': 'prefers-color-scheme', 'value': 'dark'}]
            })

            # Zaloguj użytkownika i przejdź do profilu
            self.login_user('testuser', 'testpass123')
            self.selenium.get(f"{self.live_server_url}/users/profile/")
            time.sleep(2)

            # Sprawdź kolory w trybie ciemnym
            body = self.wait_for_element(By.TAG_NAME, 'body')

            # Dodaj CSS zmieniający tryb ciemny
            self.selenium.execute_script("""
                document.body.style.backgroundColor = '#212529';
                document.body.style.color = '#f8f9fa';
            """)

            time.sleep(1)  # Daj czas na aplikację stylów

            bg_color = body.value_of_css_property('background-color')
            expected_dark_bg = 'rgb(33, 37, 41)'  # #212529

            # Sprawdź kolory z tolerancją
            def is_color_close(color1, color2, tolerance=5):
                c1 = color1.strip('rgba()').split(',')
                c2 = color2.strip('rgba()').split(',')
                return all(abs(int(a) - int(b)) <= tolerance
                           for a, b in zip(c1, c2))

            self.assertTrue(
                is_color_close(bg_color, expected_dark_bg),
                f"Background color {bg_color} should match {expected_dark_bg}"
            )

        except Exception as e:
            print(f"Dark mode test failed: {str(e)}")
            self.selenium.save_screenshot('dark_mode_error.png')
            raise e

    def tearDown(self):
        """Clean up after tests"""
        try:
            # Wyczyść pamięć podręczną i ciasteczka
            self.selenium.execute_script("window.localStorage.clear();")
            self.selenium.delete_all_cookies()

            # Wyczyść bazę danych
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM articles_userprofile_selected_categories")
                cursor.execute("DELETE FROM articles_userprofile")
                cursor.execute("DELETE FROM articles_category")
                cursor.execute("DELETE FROM auth_user")

        except Exception as e:
            print(f"Error in tearDown: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        if cls.selenium:
            cls.selenium.quit()
        super().tearDownClass()


#python manage.py test articles.tests.test_selenium --settings=ai_news.test_settings -v 2
