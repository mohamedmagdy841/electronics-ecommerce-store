import uuid
from .models import Cart, CartItem


def get_or_create_cart(request, cookie_name=None):
    """
    Returns (cart, guest_id_to_set_or_None).
    - Auth user: one cart per user.
    - Guest: cart by guest_id cookie; create + return new guest_id if missing.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart, None

    guest_id = request.COOKIES.get(cookie_name)
    if guest_id:
        cart, _ = Cart.objects.get_or_create(guest_id=guest_id)
        return cart, None

    # create new guest cart
    new_guest_id = str(uuid.uuid4())
    cart = Cart.objects.create(guest_id=new_guest_id)
    
    return cart, new_guest_id



def merge_guest_cart(request, user, cookie_name=None):
    guest_id = request.COOKIES.get(cookie_name)
    if not guest_id:
        return
    
    try:
        guest_cart = Cart.objects.get(guest_id=guest_id)
    except Cart.DoesNotExist:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)
    
    for guest_item in guest_cart.cart_items.select_related("variant"):
        stock = guest_item.variant.stock or 0
        if stock <= 0:
            continue
        
        item, created = CartItem.objects.get_or_create(
            cart=user_cart,
            variant=guest_item.variant,
            defaults={"quantity": guest_item.quantity},
        )
        if not created:
            new_qty = item.quantity + guest_item.quantity
            if new_qty > stock:
                new_qty = stock
            if new_qty != item.quantity:
                item.quantity = new_qty
                item.save(update_fields=["quantity"])
            
    guest_cart.delete()
    
    if user_cart.guest_id:
        user_cart.guest_id = None
        user_cart.save(update_fields=["guest_id"])
