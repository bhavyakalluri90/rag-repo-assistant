export async function processPayment(amount: number, method: string) {
  return {
    status: "success",
    amount,
    method,
  };
}