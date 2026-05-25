import { Button } from "./Button";
import { processPayment } from "./payment";

export function Checkout() {
  const handleCheckout = async () => {
    await processPayment(99, "credit_card");
  };

  return (
    <div>
      <h1>Checkout</h1>
      <Button label="Pay Now" onClick={handleCheckout} />
    </div>
  );
}