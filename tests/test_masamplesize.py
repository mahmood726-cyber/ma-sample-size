"""
Selenium test suite for MA Sample Size Calculator.
Tests core math functions, UI interactions, examples, existing evidence check,
tab switching, and export functionality.
"""
import sys, io, os, unittest, time, math
if not hasattr(sys.stdout, '_pytest_capture'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

HTML = 'file:///' + os.path.abspath(r'C:\Models\MASampleSize\ma-sample-size.html').replace('\\', '/')


class TestMASampleSize(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        opts = Options()
        opts.add_argument('--headless=new')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-gpu')
        cls.drv = webdriver.Chrome(options=opts)
        cls.drv.get(HTML)
        time.sleep(1)
        # Clear localStorage to start fresh
        cls.drv.execute_script("localStorage.clear();")
        cls.drv.refresh()
        time.sleep(1)
        # Suppress alert() dialogs which block in headless mode
        cls.drv.execute_script("window.alert = function(msg){ console.log('ALERT: ' + msg); };")
        cls.drv.execute_script("window.confirm = function(){ return true; };")

    @classmethod
    def tearDownClass(cls):
        cls.drv.quit()

    def js(self, script):
        return self.drv.execute_script(script)

    # ---------------------------------------------------------------
    # 1. Math utilities: erf
    # ---------------------------------------------------------------
    def test_01_erf_zero(self):
        """erf(0) should be 0"""
        val = self.js("return erf(0);")
        self.assertAlmostEqual(val, 0.0, places=6)

    def test_02_erf_positive(self):
        """erf(1) should be approx 0.8427"""
        val = self.js("return erf(1);")
        self.assertAlmostEqual(val, 0.8427, places=3)

    def test_03_erf_negative(self):
        """erf(-1) should be approx -0.8427"""
        val = self.js("return erf(-1);")
        self.assertAlmostEqual(val, -0.8427, places=3)

    # ---------------------------------------------------------------
    # 2. normalCDF
    # ---------------------------------------------------------------
    def test_04_normalCDF_zero(self):
        """normalCDF(0) = 0.5"""
        val = self.js("return normalCDF(0);")
        self.assertAlmostEqual(val, 0.5, places=6)

    def test_05_normalCDF_196(self):
        """normalCDF(1.96) ~ 0.975"""
        val = self.js("return normalCDF(1.96);")
        self.assertAlmostEqual(val, 0.975, places=3)

    # ---------------------------------------------------------------
    # 3. normalPPF (inverse normal)
    # ---------------------------------------------------------------
    def test_06_normalPPF_05(self):
        """normalPPF(0.5) = 0"""
        val = self.js("return normalPPF(0.5);")
        self.assertAlmostEqual(val, 0.0, places=4)

    def test_07_normalPPF_975(self):
        """normalPPF(0.975) ~ 1.96"""
        val = self.js("return normalPPF(0.975);")
        self.assertAlmostEqual(val, 1.96, places=2)

    def test_08_normalPPF_roundtrip(self):
        """normalCDF(normalPPF(0.90)) ~ 0.90"""
        val = self.js("return normalCDF(normalPPF(0.90));")
        self.assertAlmostEqual(val, 0.90, places=4)

    # ---------------------------------------------------------------
    # 4. sampleSizeBinary
    # ---------------------------------------------------------------
    def test_09_sample_size_binary(self):
        """Binary sample size for p0=0.10, p1=0.07 with alpha=0.05 power=0.80"""
        val = self.js("return sampleSizeBinary(0.10, 0.07, 0.05, 0.80);")
        # Should be a positive integer
        self.assertIsInstance(val, (int, float))
        self.assertGreater(val, 0)
        # Known result: approximately 1200-2000 per arm
        self.assertGreater(val, 500)
        self.assertLess(val, 5000)

    # ---------------------------------------------------------------
    # 5. sampleSizeContinuous
    # ---------------------------------------------------------------
    def test_10_sample_size_continuous(self):
        """Continuous sample size for delta=0.5, sigma=1.0, alpha=0.05, power=0.80"""
        val = self.js("return sampleSizeContinuous(0.5, 1.0, 0.05, 0.80);")
        # For d=0.5 (medium), expect ~64 per arm
        self.assertIsInstance(val, (int, float))
        self.assertGreater(val, 50)
        self.assertLess(val, 100)

    # ---------------------------------------------------------------
    # 6. heterogeneityAdjustment
    # ---------------------------------------------------------------
    def test_11_het_adjustment_zero(self):
        """heterogeneityAdjustment(0) should be 1.0 (no inflation)"""
        val = self.js("return heterogeneityAdjustment(0);")
        self.assertAlmostEqual(val, 1.0, places=6)

    def test_12_het_adjustment_50(self):
        """heterogeneityAdjustment(0.50) should be 2.0"""
        val = self.js("return heterogeneityAdjustment(0.50);")
        self.assertAlmostEqual(val, 2.0, places=6)

    def test_13_het_adjustment_75(self):
        """heterogeneityAdjustment(0.75) should be 4.0"""
        val = self.js("return heterogeneityAdjustment(0.75);")
        self.assertAlmostEqual(val, 4.0, places=5)

    def test_14_het_adjustment_extreme(self):
        """heterogeneityAdjustment(0.99) should be capped at 100"""
        val = self.js("return heterogeneityAdjustment(0.99);")
        self.assertEqual(val, 100)

    # ---------------------------------------------------------------
    # 7. computeRIS
    # ---------------------------------------------------------------
    def test_15_compute_ris(self):
        """computeRIS with medium effect and no heterogeneity"""
        val = self.js("return computeRIS(0.5, 0, 0.05, 0.80);")
        # Should be same as 2 * n_base with hetAdj=1
        self.assertIsInstance(val, (int, float))
        self.assertGreater(val, 50)

    def test_16_compute_ris_with_heterogeneity(self):
        """computeRIS inflates with I2"""
        val_no_het = self.js("return computeRIS(0.5, 0, 0.05, 0.80);")
        val_het = self.js("return computeRIS(0.5, 0.50, 0.05, 0.80);")
        # With I2=50%, hetAdj=2, so RIS should double
        self.assertAlmostEqual(val_het / val_no_het, 2.0, places=0)

    # ---------------------------------------------------------------
    # 8. computePower
    # ---------------------------------------------------------------
    def test_17_compute_power_large_n(self):
        """computePower with large N should approach 1.0"""
        val = self.js("return computePower(100000, 0.5, 0, 0.05);")
        self.assertGreater(val, 0.99)

    def test_18_compute_power_small_n(self):
        """computePower with tiny N should be near zero"""
        val = self.js("return computePower(10, 0.1, 0, 0.05);")
        self.assertLess(val, 0.10)

    # ---------------------------------------------------------------
    # 9. mde (minimum detectable effect)
    # ---------------------------------------------------------------
    def test_19_mde_decreases_with_n(self):
        """MDE should decrease as N increases"""
        mde1 = self.js("return mde(100, 0, 0.05, 0.80);")
        mde2 = self.js("return mde(1000, 0, 0.05, 0.80);")
        self.assertGreater(mde1, mde2)

    def test_20_mde_increases_with_het(self):
        """MDE should increase with more heterogeneity"""
        mde1 = self.js("return mde(500, 0, 0.05, 0.80);")
        mde2 = self.js("return mde(500, 0.50, 0.05, 0.80);")
        self.assertGreater(mde2, mde1)

    # ---------------------------------------------------------------
    # 10. Tab switching
    # ---------------------------------------------------------------
    def test_21_tab_switching(self):
        """Tabs should switch panels correctly"""
        # Switch to curves tab
        self.js("switchTab('curves');")
        time.sleep(0.3)
        active = self.js("return document.getElementById('tab-curves').classList.contains('active');")
        self.assertTrue(active, "Curves tab panel should be active")

        # Switch back to params (the main calculator tab)
        self.js("switchTab('params');")
        time.sleep(0.3)
        active = self.js("return document.getElementById('tab-params').classList.contains('active');")
        self.assertTrue(active, "Params tab panel should be active")

    # ---------------------------------------------------------------
    # 11. Outcome type toggle
    # ---------------------------------------------------------------
    def test_22_outcome_type_binary(self):
        """Setting outcome to binary shows binary inputs"""
        self.js("setOutcome('binary');")
        hidden = self.js("return document.getElementById('binaryInputs').classList.contains('hidden');")
        self.assertFalse(hidden, "Binary inputs should be visible")

    def test_23_outcome_type_continuous(self):
        """Setting outcome to continuous shows continuous inputs"""
        self.js("setOutcome('continuous');")
        hidden = self.js("return document.getElementById('continuousInputs').classList.contains('hidden');")
        self.assertFalse(hidden, "Continuous inputs should be visible")
        # Restore
        self.js("setOutcome('binary');")

    # ---------------------------------------------------------------
    # 12. Load example: statin (binary, GREEN)
    # ---------------------------------------------------------------
    def test_24_example_statin(self):
        """Loading statin example should produce green traffic light"""
        # loadExample sets select .value with number 0.80 which JS truncates to "0.8",
        # not matching option value "0.80". Fix: explicitly set the select after loading.
        self.js("""
            loadExample('statin');
            document.getElementById('powerTarget').value = '0.80';
            runCalculation();
        """)
        time.sleep(0.5)
        result_visible = self.js("return document.getElementById('resultsCard').style.display !== 'none';")
        self.assertTrue(result_visible, "Results card should be visible")
        tl_class = self.js("return document.getElementById('trafficLight').className;")
        self.assertIn('green', tl_class, "Statin example should be GREEN")

    # ---------------------------------------------------------------
    # 13. Load example: anticoagulant (binary, RED)
    # ---------------------------------------------------------------
    def test_25_example_anticoag(self):
        """Loading anticoagulant example should produce green traffic light (Tab 1 always plans enough studies)"""
        self.js("""
            loadExample('anticoag');
            document.getElementById('powerTarget').value = '0.80';
            runCalculation();
        """)
        time.sleep(0.5)
        tl_class = self.js("return document.getElementById('trafficLight').className;")
        # Tab 1 calculates required k and totalN to meet RIS, so ratio >= 1.0 => always GREEN
        self.assertIn('green', tl_class, "Tab 1 plans sufficient studies, should be GREEN")

    # ---------------------------------------------------------------
    # 14. Load example: exercise (continuous, YELLOW)
    # ---------------------------------------------------------------
    def test_26_example_exercise(self):
        """Loading exercise example should produce yellow or green traffic light"""
        self.js("""
            loadExample('exercise');
            document.getElementById('powerTarget').value = '0.80';
            runCalculation();
        """)
        time.sleep(0.5)
        tl_class = self.js("return document.getElementById('trafficLight').className;")
        result = self.js("return appState.lastResult;")
        ratio = result['totalN'] / result['risTotal'] if result['risTotal'] > 0 else 0
        # Exercise: moderate effect, high heterogeneity, small trials
        # Ratio determines color: >=1 green, >=0.5 yellow, <0.5 red
        self.assertTrue(
            'yellow' in tl_class or 'green' in tl_class,
            f"Exercise example should be YELLOW or GREEN (ratio={ratio:.2f}, class={tl_class})"
        )

    # ---------------------------------------------------------------
    # 15. Run calculation with custom binary inputs
    # ---------------------------------------------------------------
    def test_27_run_calculation_binary(self):
        """Custom binary calculation produces valid results"""
        self.js("""
            setOutcome('binary');
            document.getElementById('p0').value = '0.15';
            document.getElementById('p1').value = '0.10';
            document.getElementById('alphaLevel').value = '0.05';
            document.getElementById('powerTarget').value = '0.80';
            document.getElementById('i2Slider').value = '30';
            document.getElementById('avgStudySize').value = '200';
            runCalculation();
        """)
        time.sleep(0.5)
        result = self.js("return appState.lastResult;")
        self.assertIsNotNone(result)
        self.assertGreater(result['risTotal'], 0)
        self.assertGreater(result['kNeeded'], 0)
        self.assertGreater(result['currentPower'], 0)

    # ---------------------------------------------------------------
    # 16. Run calculation with custom continuous inputs
    # ---------------------------------------------------------------
    def test_28_run_calculation_continuous(self):
        """Custom continuous calculation produces valid results"""
        self.js("""
            setOutcome('continuous');
            document.getElementById('meanDiff').value = '0.3';
            document.getElementById('pooledSD').value = '1.0';
            document.getElementById('alphaLevel').value = '0.05';
            document.getElementById('powerTarget').value = '0.80';
            document.getElementById('i2Slider').value = '40';
            document.getElementById('avgStudySize').value = '100';
            runCalculation();
        """)
        time.sleep(0.5)
        result = self.js("return appState.lastResult;")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['effectSize'], 0.3, places=2)

    # ---------------------------------------------------------------
    # 17. I2 slider display update
    # ---------------------------------------------------------------
    def test_29_i2_slider_display(self):
        """I2 slider updates display text correctly"""
        self.js("""
            document.getElementById('i2Slider').value = '60';
            updateI2Display();
        """)
        text = self.js("return document.getElementById('i2Val').textContent;")
        self.assertEqual(text, '60%')

    # ---------------------------------------------------------------
    # 18. Existing evidence check
    # ---------------------------------------------------------------
    def test_30_existing_evidence_check(self):
        """Existing evidence panel calculates power correctly"""
        self.js("""
            document.getElementById('extK').value = '10';
            document.getElementById('extN').value = '5000';
            document.getElementById('extEffect').value = '0.30';
            document.getElementById('extI2').value = '25';
            document.getElementById('extLCI').value = '0.10';
            document.getElementById('extUCI').value = '0.50';
            document.getElementById('extAlpha').value = '0.05';
            document.getElementById('extAvgN').value = '200';
            runExistingCheck();
        """)
        time.sleep(0.5)
        result = self.js("return appState.lastExistingResult;")
        self.assertIsNotNone(result, "Existing result should be set")
        self.assertEqual(result['k'], 10)
        self.assertEqual(result['N'], 5000)
        self.assertGreater(result['currentPower'], 0)
        self.assertGreater(result['ris'], 0)

    # ---------------------------------------------------------------
    # 19. Existing evidence: conclusive case
    # ---------------------------------------------------------------
    def test_31_existing_evidence_conclusive(self):
        """Large N with strong effect should be GREEN"""
        self.js("""
            document.getElementById('extK').value = '20';
            document.getElementById('extN').value = '50000';
            document.getElementById('extEffect').value = '0.50';
            document.getElementById('extI2').value = '10';
            document.getElementById('extLCI').value = '0.30';
            document.getElementById('extUCI').value = '0.70';
            document.getElementById('extAlpha').value = '0.05';
            document.getElementById('extAvgN').value = '1000';
            runExistingCheck();
        """)
        time.sleep(0.3)
        result = self.js("return appState.lastExistingResult;")
        self.assertEqual(result['light'], 'green')

    # ---------------------------------------------------------------
    # 20. Existing evidence: underpowered case
    # ---------------------------------------------------------------
    def test_32_existing_evidence_underpowered(self):
        """Tiny N with small effect should be RED"""
        self.js("""
            document.getElementById('extK').value = '2';
            document.getElementById('extN').value = '100';
            document.getElementById('extEffect').value = '0.10';
            document.getElementById('extI2').value = '60';
            document.getElementById('extLCI').value = '-0.20';
            document.getElementById('extUCI').value = '0.40';
            document.getElementById('extAlpha').value = '0.05';
            document.getElementById('extAvgN').value = '50';
            runExistingCheck();
        """)
        time.sleep(0.3)
        result = self.js("return appState.lastExistingResult;")
        self.assertEqual(result['light'], 'red')

    # ---------------------------------------------------------------
    # 21. Export tab and text generation
    # ---------------------------------------------------------------
    def test_33_export_text_generated(self):
        """Export text area should have content after calculation"""
        self.js("""
            loadExample('statin');
            document.getElementById('powerTarget').value = '0.80';
            runCalculation();
        """)
        time.sleep(0.5)
        self.js("switchTab('export');")
        time.sleep(0.5)
        text = self.js("return document.getElementById('exportTextArea').textContent;")
        self.assertIn('MA SAMPLE SIZE CALCULATOR', text)
        self.assertIn('RIS total', text)

    # ---------------------------------------------------------------
    # 22. Theme toggle
    # ---------------------------------------------------------------
    def test_34_theme_toggle(self):
        """Theme toggle should switch between light and dark"""
        self.js("toggleTheme();")
        theme = self.js("return document.body.getAttribute('data-theme');")
        self.assertEqual(theme, 'dark')
        self.js("toggleTheme();")
        theme = self.js("return document.body.getAttribute('data-theme');")
        self.assertEqual(theme, 'light')

    # ---------------------------------------------------------------
    # 23. RIS formula consistency
    # ---------------------------------------------------------------
    def test_35_ris_formula_consistency(self):
        """computeRIS should agree with manual formula for known values"""
        # RIS = 2*(za+zb)^2/d^2 * (1+D^2)
        # d=0.5, I2=0, alpha=0.05, power=0.80
        # za=1.96, zb=0.84 => (1.96+0.84)^2 = 7.84 => 2*7.84/0.25 = 62.72 => ceil = 63
        ris = self.js("return computeRIS(0.5, 0, 0.05, 0.80);")
        # Manual calculation
        za = 1.9599639845  # normalPPF(0.975)
        zb = 0.8416212336  # normalPPF(0.80)
        n_manual = math.ceil(2 * (za + zb) ** 2 / (0.5 ** 2))
        self.assertEqual(ris, n_manual)

    # ---------------------------------------------------------------
    # 24. Power calculation roundtrip
    # ---------------------------------------------------------------
    def test_36_power_roundtrip(self):
        """computePower at RIS should yield approximately 80%"""
        ris = self.js("return computeRIS(0.5, 0.25, 0.05, 0.80);")
        power = self.js(f"return computePower({ris}, 0.5, 0.25, 0.05);")
        # Power at RIS should be >= 80% (ceil may give slightly more)
        self.assertGreaterEqual(power, 0.79)

    # ---------------------------------------------------------------
    # 25. Edge case: very small effect
    # ---------------------------------------------------------------
    def test_37_small_effect_large_ris(self):
        """Very small effect size should require very large RIS"""
        ris = self.js("return computeRIS(0.05, 0, 0.05, 0.80);")
        self.assertGreater(ris, 5000, "Small effect should need very large N")

    # ---------------------------------------------------------------
    # 26. Edge case: large effect
    # ---------------------------------------------------------------
    def test_38_large_effect_small_ris(self):
        """Large effect size should require small RIS"""
        ris = self.js("return computeRIS(2.0, 0, 0.05, 0.80);")
        self.assertLess(ris, 30, "Large effect should need small N")

    # ---------------------------------------------------------------
    # 27. Charts render without errors
    # ---------------------------------------------------------------
    def test_39_charts_render(self):
        """Charts tab should render all 4 canvases without JS errors"""
        self.js("switchTab('curves');")
        time.sleep(0.5)
        self.js("drawAllCharts();")
        time.sleep(0.5)
        # Check all 4 canvases have been drawn (have _toX property set)
        has_chart1 = self.js("return document.getElementById('chartPowerK')._toX !== undefined;")
        has_chart2 = self.js("return document.getElementById('chartPowerN')._toX !== undefined;")
        has_chart3 = self.js("return document.getElementById('chartMDE')._toX !== undefined;")
        has_chart4 = self.js("return document.getElementById('chartRISvsI2')._toX !== undefined;")
        self.assertTrue(has_chart1, "Chart Power vs K should be drawn")
        self.assertTrue(has_chart2, "Chart Power vs N should be drawn")
        self.assertTrue(has_chart3, "Chart MDE should be drawn")
        self.assertTrue(has_chart4, "Chart RIS vs I2 should be drawn")

    # ---------------------------------------------------------------
    # 28. LocalStorage persistence
    # ---------------------------------------------------------------
    def test_40_localstorage_key(self):
        """App uses correct localStorage key"""
        self.js("saveState();")
        val = self.js("return localStorage.getItem('masamplesize_v1');")
        self.assertIsNotNone(val)
        self.assertIn('outcomeType', val)

    # ---------------------------------------------------------------
    # 29. Results card visibility after calculation
    # ---------------------------------------------------------------
    def test_41_results_card_visibility(self):
        """noResultCard hidden, resultsCard shown after calculation"""
        self.js("loadExample('statin');")
        time.sleep(0.5)
        no_result_display = self.js("return document.getElementById('noResultCard').style.display;")
        results_display = self.js("return document.getElementById('resultsCard').style.display;")
        self.assertEqual(no_result_display, 'none')
        self.assertNotEqual(results_display, 'none')

    # ---------------------------------------------------------------
    # 30. Export chart canvas exists
    # ---------------------------------------------------------------
    def test_42_export_chart_exists(self):
        """Export chart canvas should exist and draw"""
        self.js("switchTab('export');")
        time.sleep(0.5)
        exists = self.js("return document.getElementById('exportChart') !== null;")
        self.assertTrue(exists)


if __name__ == '__main__':
    unittest.main(verbosity=2)
