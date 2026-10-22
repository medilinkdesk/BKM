// Donation Handler for Razorpay, Cashfree & Direct UPI QR

let selectedAmount = 1100;
let selectedGateway = 'RAZORPAY';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Amount selection buttons
    const amountBtns = document.querySelectorAll('.amount-btn');
    const customAmountInput = document.getElementById('customAmount');

    amountBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            amountBtns.forEach(b => {
                b.classList.remove('bg-mandir-red', 'text-white', 'border-mandir-red');
                b.classList.add('bg-white', 'text-gray-800', 'border-gray-300');
            });
            btn.classList.remove('bg-white', 'text-gray-800', 'border-gray-300');
            btn.classList.add('bg-mandir-red', 'text-white', 'border-mandir-red');
            
            selectedAmount = parseFloat(btn.dataset.amount);
            if (customAmountInput) customAmountInput.value = selectedAmount;
            updateSummaryDisplay();
        });
    });

    if (customAmountInput) {
        customAmountInput.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            if (!isNaN(val) && val > 0) {
                selectedAmount = val;
                // deselect preset buttons if custom
                amountBtns.forEach(b => {
                    if (parseFloat(b.dataset.amount) === val) {
                        b.classList.add('bg-mandir-red', 'text-white', 'border-mandir-red');
                    } else {
                        b.classList.remove('bg-mandir-red', 'text-white', 'border-mandir-red');
                        b.classList.add('bg-white', 'text-gray-800', 'border-gray-300');
                    }
                });
                updateSummaryDisplay();
            }
        });
    }

    // 2. Gateway selection
    const gatewayRadios = document.querySelectorAll('input[name="gateway"]');
    gatewayRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            selectedGateway = e.target.value;
            updateGatewayUI();
            updateSummaryDisplay();
        });
    });

    // 3. Donation Form Submission
    const donationForm = document.getElementById('mandirDonationForm');
    if (donationForm) {
        donationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await processDonation();
        });
    }
});

function updateGatewayUI() {
    const upiContainer = document.getElementById('upiQrContainer');
    if (upiContainer) {
        if (selectedGateway === 'UPI_QR') {
            upiContainer.classList.remove('hidden');
        } else {
            upiContainer.classList.add('hidden');
        }
    }
}

function updateSummaryDisplay() {
    const summaryAmt = document.getElementById('summaryAmount');
    if (summaryAmt) {
        summaryAmt.textContent = `₹${selectedAmount.toLocaleString('en-IN')}`;
    }
}

async function processDonation() {
    const submitBtn = document.getElementById('submitDonationBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> कृपया प्रतीक्षा करें...`;

    try {
        const donorName = document.getElementById('donor_name').value.trim();
        const phone = document.getElementById('donor_phone').value.trim();
        const email = document.getElementById('donor_email').value.trim();
        const pan = document.getElementById('donor_pan').value.trim();
        const address = document.getElementById('donor_address').value.trim();
        const gotra = document.getElementById('donor_gotra').value.trim();
        const purpose = document.getElementById('donation_purpose').value;

        if (!donorName || !phone) {
            alert('कृपया अपना नाम और मोबाइल नंबर दर्ज करें।');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            return;
        }

        if (phone.length < 10) {
            alert('कृपया वैध 10 अंकों का मोबाइल नंबर दर्ज करें।');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            return;
        }

        // Call backend initiate
        const response = await fetch('/api/donation/initiate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                donor_name: donorName,
                phone: phone,
                email: email,
                pan: pan,
                address: address,
                gotra: gotra,
                purpose: purpose,
                amount: selectedAmount,
                gateway: selectedGateway
            })
        });

        const data = await response.json();

        if (data.status !== 'success') {
            alert(data.message || 'त्रुटि हुई। कृपया पुनः प्रयास करें।');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            return;
        }

        // Handle specific gateways
        if (selectedGateway === 'RAZORPAY') {
            handleRazorpayPayment(data, submitBtn, originalText);
        } else if (selectedGateway === 'CASHFREE') {
            handleCashfreePayment(data, submitBtn, originalText);
        } else if (selectedGateway === 'UPI_QR') {
            handleUpiQrPayment(data, submitBtn, originalText);
        }

    } catch (err) {
        console.error('Donation initiation error:', err);
        alert('सर्वर से संपर्क करने में समस्या हुई। कृपया पुनः प्रयास करें।');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// ------------------------------------------
// 1. RAZORPAY HANDLER
// ------------------------------------------
function handleRazorpayPayment(data, submitBtn, originalText) {
    // If running in test mode with mock order, simulate friendly completion dialog
    if (data.is_test_mode) {
        showSimulatedPaymentModal('Razorpay Gateway (Test Mode)', data.amount / 100, async () => {
            const verifyRes = await fetch('/api/payment/razorpay/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    donation_id: data.donation_id,
                    razorpay_order_id: data.order_id,
                    razorpay_payment_id: `pay_test_rzp_${Date.now()}`,
                    razorpay_signature: 'test_signature_valid',
                    receipt_no: data.receipt_no
                })
            });
            const vData = await verifyRes.json();
            if (vData.status === 'success') {
                window.location.href = vData.redirect_url;
            } else {
                alert('Verification failed: ' + vData.message);
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        });
        return;
    }

    // Live Razorpay Checkout
    const options = {
        key: data.key_id,
        amount: data.amount,
        currency: data.currency,
        name: "श्री श्री १०८ बूढ़ी काली मंदिर",
        description: `पावन दान सेवा - ${data.receipt_no}`,
        order_id: data.order_id,
        prefill: {
            name: data.donor_name,
            contact: data.phone,
            email: data.email
        },
        theme: {
            color: "#881337"
        },
        handler: async function (response) {
            submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> रसीद तैयार हो रही है...`;
            const verifyRes = await fetch('/api/payment/razorpay/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    donation_id: data.donation_id,
                    razorpay_order_id: response.razorpay_order_id,
                    razorpay_payment_id: response.razorpay_payment_id,
                    razorpay_signature: response.razorpay_signature,
                    receipt_no: data.receipt_no
                })
            });
            const vData = await verifyRes.json();
            if (vData.status === 'success') {
                window.location.href = vData.redirect_url;
            } else {
                alert('Payment verification failed: ' + vData.message);
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        },
        modal: {
            ondismiss: function () {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        }
    };

    const rzp = new Razorpay(options);
    rzp.open();
}

// ------------------------------------------
// 2. CASHFREE HANDLER
// ------------------------------------------
function handleCashfreePayment(data, submitBtn, originalText) {
    // If in test mode or simulated session
    if (data.is_test_mode) {
        showSimulatedPaymentModal('Cashfree Payments (Test Mode)', selectedAmount, () => {
            window.location.href = `/payment/cashfree/return?receipt_no=${data.receipt_no}&order_id=${data.order_id}`;
        });
        return;
    }

    // Cashfree Drop Checkout
    try {
        const cashfree = Cashfree({
            mode: data.environment === 'production' ? 'production' : 'sandbox'
        });

        cashfree.checkout({
            paymentSessionId: data.payment_session_id,
            redirectTarget: "_self"
        });
    } catch (err) {
        console.error('Cashfree SDK initialization failed, redirecting to fallback', err);
        window.location.href = `/payment/cashfree/return?receipt_no=${data.receipt_no}&order_id=${data.order_id}`;
    }
}

// ------------------------------------------
// 3. DIRECT UPI QR CODE HANDLER
// ------------------------------------------
function handleUpiQrPayment(data, submitBtn, originalText) {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;

    // Show UPI Modal
    const upiModal = document.getElementById('upiQrModal');
    const qrImage = document.getElementById('upiQrImage');
    const modalUpiId = document.getElementById('modalUpiId');
    const modalAmount = document.getElementById('modalUpiAmount');
    const modalReceiptNo = document.getElementById('modalUpiReceiptNo');
    const donationIdInput = document.getElementById('modalUpiDonationId');

    if (modalUpiId) modalUpiId.textContent = data.upi_id;
    if (modalAmount) modalAmount.textContent = `₹${data.amount.toLocaleString('en-IN')}`;
    if (modalReceiptNo) modalReceiptNo.textContent = data.receipt_no;
    if (donationIdInput) donationIdInput.value = data.donation_id;

    // Generate dynamic QR code using Google Chart / QuickChart API or direct SVG
    const encodedUpiUrl = encodeURIComponent(data.upi_url);
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodedUpiUrl}&color=88-19-55`;
    if (qrImage) qrImage.src = qrUrl;

    if (upiModal) upiModal.classList.remove('hidden');
}

// Submit UTR Number
async function submitUpiUtr() {
    const utrInput = document.getElementById('utrNumberInput');
    const utrVal = utrInput ? utrInput.value.trim() : '';
    const donationId = document.getElementById('modalUpiDonationId').value;
    const receiptNo = document.getElementById('modalUpiReceiptNo').textContent;
    const submitUtrBtn = document.getElementById('submitUtrBtn');

    if (!utrVal || utrVal.length < 6) {
        alert('कृपया अपने PhonePe, Google Pay या Paytm से 12 अंकों का UTR / Transaction No. दर्ज करें।');
        return;
    }

    submitUtrBtn.disabled = true;
    submitUtrBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> सत्यापन जारी है...`;

    try {
        const res = await fetch('/api/payment/upi/submit-utr', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                donation_id: donationId,
                utr_no: utrVal,
                receipt_no: receiptNo
            })
        });

        const data = await res.json();
        if (data.status === 'success') {
            window.location.href = data.redirect_url;
        } else {
            alert(data.message || 'त्रुटि हुई। कृपया पुनः प्रयास करें।');
            submitUtrBtn.disabled = false;
            submitUtrBtn.innerHTML = `सत्यापित करें एवं रसीद पाएं`;
        }
    } catch (err) {
        console.error('UTR submission error', err);
        alert('सर्वर से संपर्क नहीं हो सका।');
        submitUtrBtn.disabled = false;
        submitUtrBtn.innerHTML = `सत्यापित करें एवं रसीद पाएं`;
    }
}

// Modal helper for Test/Demo mode
function showSimulatedPaymentModal(gatewayTitle, amount, onComplete) {
    const modal = document.createElement('div');
    modal.className = "fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fade-in";
    modal.innerHTML = `
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border-2 border-mandir-gold text-center space-y-4">
            <div class="w-16 h-16 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center mx-auto text-2xl border border-amber-300">
                <i class="fa-solid fa-shield-halved"></i>
            </div>
            <h3 class="font-bold text-xl text-mandir-maroon font-yatra">${gatewayTitle}</h3>
            <p class="text-xs text-gray-600">
                यह मंदिर पोर्टल का परीक्षण (Demo / Test Sandbox) मोड है। लाइव पेमेंट गेटवे क्रेडेंशियल्स दर्ज करने से पूर्व पूरे दान एवं रसीद प्रवाह का परीक्षण करने के लिए इसे बनाया गया है।
            </p>
            <div class="bg-amber-50 p-4 rounded-xl border border-amber-200">
                <p class="text-xs text-gray-500">दान राशि (Test Amount)</p>
                <p class="text-2xl font-bold text-mandir-red font-mono">₹${parseFloat(amount).toLocaleString('en-IN')}</p>
            </div>
            <div class="flex gap-3 pt-2">
                <button id="cancelSimBtn" class="flex-1 py-2.5 px-4 rounded-xl border border-gray-300 font-semibold text-gray-700 hover:bg-gray-100 transition text-sm">
                    रद्द करें (Cancel)
                </button>
                <button id="completeSimBtn" class="flex-1 py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-green-600 font-bold text-white hover:from-emerald-700 hover:to-green-700 transition shadow-md text-sm flex items-center justify-center gap-1.5">
                    <i class="fa-solid fa-check"></i> सफल दान पूर्ण करें
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    document.getElementById('cancelSimBtn').addEventListener('click', () => {
        modal.remove();
        const submitBtn = document.getElementById('submitDonationBtn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fa-solid fa-hands-praying mr-2 text-yellow-300"></i> दान पूर्ण करें (Proceed to Donate)`;
        }
    });

    document.getElementById('completeSimBtn').addEventListener('click', () => {
        modal.remove();
        onComplete();
    });
}
