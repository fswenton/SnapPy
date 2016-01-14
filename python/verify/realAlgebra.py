from ..sage_helper import _within_sage, sage_method, SageNotAvailable

__all__ = ['field_containing_real_and_imaginary_part_of_number_field']

if _within_sage:
    from sage.rings.rational_field import RationalField
    from sage.rings.polynomial.polynomial_ring_constructor import PolynomialRing
    from sage.rings.number_field.number_field import NumberField
    from sage.rings.complex_interval_field import ComplexIntervalField
    from sage.rings.real_mpfi import RealIntervalField
    from sage.symbolic.ring import var
    from sage.functions.other import binomial

class _IsolateFactorError(RuntimeError):
    """
    Exception raised by _find_unique_good_factor.
    """

def _find_unique_good_factor(polynomial, eval_method):
    """
    Given a Sage polynomial, factor it. Return the unique factor for which the
    given eval_method returns an interval containing zero. If no or more than
    one factor have this property, raise an exception.
    """

    # Factor polynomial. Call eval_method on each factor which is suppsed to
    # return an interval. Get those factors for which the resulting interval
    # contains 0.
    good_factors = [ factor
                     for factor, multiplicity in polynomial.factor()
                     if 0 in eval_method(factor)]
    
    # No unique factor, bail with an exception.
    if not len(good_factors) == 1:
        raise _IsolateFactorError()

    return good_factors[0]

def _solve_two_equations(eqn1, eqn2, x_val, y_val):
    """
    Given two polynomial equations with rational coefficients in 'x' and 'y'
    and real intervals for x and y to isolate a solution to the system of
    equations, return the number field generated by x and the value of y in
    that number field. If y is not contained in the number field generated
    by x, return None.
    """

    # Ring we work in Q[x][y]
    Rx = PolynomialRing(RationalField(), 'x')
    R  = PolynomialRing(Rx, 'y')
    Reqn1 = R(eqn1)

    # Compute the resultant in Q[x]
    resultant = Reqn1.resultant(R(eqn2))

    # Factorize the resultant. Find the unique factor that has the given value
    # for x as a root.
    def eval_factor_res(p):
        """
        Evaluation method for the factors of the resultant. Apply polynomial
        to the given interval for x.
        """
        return p(x_val)
    resultant_factor = _find_unique_good_factor(resultant, eval_factor_res)

    resultant_factor = Rx(resultant_factor)
    
    # The number field generated by x.
    #
    # (The embedding passed to the NumberField is a real number, so sage
    # will raise an exception if the resultant_factor has no real roots.
    # However, such a factor should not make it through
    #    _find_unique_good_factor)

    result_number_field = NumberField(resultant_factor, 'x',
                                      embedding = x_val.center())
    
    # Get one of the equations and think of it as an element in NumberField[y]
    yEqn = Reqn1.change_ring(result_number_field)

    # Factorize that equation over the NumberField. Find the unique factor
    # such that the given value y is a root when setting x to the given value
    # for x.
    def eval_factor_yEqn(p):
        """
        Evaluation method for the factors of the equation factored over the
        number field. We take the factor and turn it into a polynomial in
        Q[x][y]. We then put in the given intervals for x and y.
        """

        result = 0
        
        for cy, ey in zip(p.coefficients(), p.exponents()):
            cy_lift = cy.lift()
            for cx, ex in zip(cy_lift.coefficients(), cy_lift.exponents()):
                
                result += cx * (x_val ** ex) * (y_val ** ey)

        return result

        # Bad Bad Sage!!!
        # This used to work in sage 6.7 but is broken in sage 6.10!
    
        lift = p.map_coefficients(lambda c:c.lift('x'), R)
        return lift.substitute(x = x_val, y = y_val)
    
    yEqn_factor = _find_unique_good_factor(yEqn, eval_factor_yEqn)

    # If the equation for y in x is not of degree 1, then y is in a field
    # extension of the number field generated by x.
    # Bail if this happens.
    if not yEqn_factor.degree() == 1:
        return None

    # The equation of y is of the form
    #     linear_term * y + constant_term = 0
    constant_term, linear_term = yEqn_factor.coefficients(sparse = False)

    # Thus, y is given by - constant_term / linear_term
    return result_number_field, - constant_term / linear_term


def _real_or_imaginary_part_of_power_of_complex_number(n, start):
    """
    Let z = x + y * I.
    If start = 0, return Re(z^n). If start = 1, return Im(z^n).
    The result is a sage symbolic expression in x and y with rational
    coefficients.
    """

    # By binomial theorem, we have
    #
    #               n       n        n       n    n-i    i
    #   (x + y * I)   = sum       (     ) * I  * x    * y
    #                     i = 0      i
    #
    # The real/imaginary part consists of all even/odd terms in the sum:
    return sum([
        binomial(n, i) * (-1) ** (i/2) * var('x') ** (n - i) * var('y') ** i
        for i in range(start, n + 1, 2)])

def _real_or_imaginary_part_for_polynomial_in_complex_variable(polynomial,
                                                               start):
    """
    Given a polynomial p with rational coefficients, return the 
    real (start = 0) / imaginary (start = 1) part of p(x + y * I).
    The result is a sage symbolic expression in x and y with rational
    coefficients.
    """
    # Get the real/imaginary part of (x + y * I)^i and multiply by
    # the corresponding coefficient of the polynomial. Sum it all up.

    return sum([
        coeff * _real_or_imaginary_part_of_power_of_complex_number(i, start)
        for i, coeff in enumerate(polynomial.coefficients(sparse = False))])
    
@sage_method
def field_containing_real_and_imaginary_part_of_number_field(number_field):
    """
    Given a Sage number field number_field with a complex embedding z, return
               (real_number_field, real_part, imag_part).

    The number field real_number_field is the smallest number field containing
    the real part and imaginary part of very element in number_field.

    real_part and imag_part are elements in real_number_field which comes with
    a real embedding such that under this embedding, we have
               z = real_part + imag_part * I.

        sage: from sage.rings.complex_field import ComplexField
        sage: CF = ComplexField()
        sage: x = var('x')
        sage: nf = NumberField(x**2 + 1, 'x', embedding = CF(1.0j))
        sage: field_containing_real_and_imaginary_part_of_number_field(nf)
        (Number Field in x with defining polynomial x, 0, 1)

        sage: nf = NumberField(x**2 + 7, 'x', embedding = CF(2.64575j))
        sage: field_containing_real_and_imaginary_part_of_number_field(nf)
        (Number Field in x with defining polynomial x^2 - 7, 0, x)

        sage: nf = NumberField(x**3 + x**2 + 23, 'x', embedding = CF(1.1096 + 2.4317j))
        sage: field_containing_real_and_imaginary_part_of_number_field(nf)
        (Number Field in x with defining polynomial x^6 + 2*x^5 + 2*x^4 - 113/2*x^3 - 229/4*x^2 - 115/4*x - 575/8, -20/14377*x^5 + 382/14377*x^4 + 526/14377*x^3 + 1533/14377*x^2 - 18262/14377*x - 10902/14377, 20/14377*x^5 - 382/14377*x^4 - 526/14377*x^3 - 1533/14377*x^2 + 32639/14377*x + 10902/14377)
    """

    # Let p be the defining polynomial of the given number field.
    # Given the one complex equation p(z) = 0, translate it into two
    # real equations Re(p(x+y*I)) = 0, Im(p(x+y*I)) = 0.
    # equations are sage symbolic expressions in x and y.
    equations = [ 
      _real_or_imaginary_part_for_polynomial_in_complex_variable(
          number_field.defining_polynomial(), start)
      for start in [0, 1]]

    # In _solve_two_equations, we implemented a method that can solve
    # a system of two polynomial equations in two variables x and y
    # provided that y is in the number field generated by x.
    # If we are lucky, this is the case.
    # If we are unlucky, the number field containing x and y is generated
    # by x' = x + k * y where k is some small natural number.

    # The k mentioned above. We start with 0 and increase until we
    # succeed.
    k = 0

    # The amount of extra precision beyond double precision we are working
    # with. We increase it if one of the above methods fails to find the right
    # factor of the above polynomials.
    extra_prec = 0

    # Initialize the intervals for x and y with double prescision intervals
    CIF = ComplexIntervalField()
    z_val = CIF(number_field.gen_embedding())
    x_val = z_val.real()
    y_val = z_val.imag()

    # Keep trying to find a k or increase precision until we succeed
    # Give up if k reaches 100 or we are at precision 16 times greater than
    # that of a double
    while k < 100 and extra_prec < 5:

        # Compute the interval for x'
        xprime_val = x_val + k * y_val

        # From the equations for x and y, get the equations for x' and y
        # where x' = x + k * y as abover
        equations_for_xprime = [ eqn.substitute(x = var('x') - k * var('y'))
                                 for eqn in equations ]

        try:
            # Try to find a solution to the two equations
            solution = _solve_two_equations(equations_for_xprime[0],
                                            equations_for_xprime[1],
                                            xprime_val, y_val)

            if solution:
                # We succeeded. We have a solution for the equations in
                # x' and y, thus, we need to do x = x' - k * y
                real_number_field, y_expression = solution
                x_expression = real_number_field.gen() - k * y_expression
                return real_number_field, x_expression, y_expression
            else:
                # No solution found. This means that y is not in the
                # number field generated by x'. Try a higher k in the
                # next iteration
                k += 1

        except _IsolateFactorError:
            # We did not use enough precision. The given intervals for
            # x and y that are supposed to isolate a solution to the
            # system of two equations did not have enough precision to
            # succeed and give a unique answer.

            # Double the precision we will use from now on
            extra_prec += 1

            # Recompute the intervals for x and y with the new precision.
            CIF = ComplexIntervalField(53 * 2 ** extra_prec)
            z_val = CIF(number_field.gen_embedding())
            x_val = z_val.real()
            y_val = z_val.imag()

    # Give up
    return None

def _test_result(number_field, prec = 53, epsilon = 1e-10):
    """
        sage: from sage.rings.complex_field import ComplexField
        sage: CF = ComplexField()
        sage: x = var('x')
        sage: nf = NumberField(x**2 + 1, 'x', embedding = CF(1.0j))
        sage: _test_result(nf)
        sage: nf = NumberField(x**2 + 7, 'x', embedding = CF(2.64575j))
        sage: _test_result(nf)
        sage: nf = NumberField(x**8 + 6 * x ** 4 + x + 23, 'x', embedding = CF(0.7747 + 1.25937j))
        sage: _test_result(nf, 212, epsilon = 1e-30)
    """


    CIF = ComplexIntervalField(prec)
    RIF = RealIntervalField(prec)

    real_number_field, x_expression, y_expression = (
        field_containing_real_and_imaginary_part_of_number_field(number_field))

    x_val = x_expression.lift()(RIF(real_number_field.gen_embedding()))
    y_val = y_expression.lift()(RIF(real_number_field.gen_embedding()))
    z_val = CIF(x_val, y_val)

    diff = z_val - CIF(number_field.gen_embedding())

    if not abs(diff) < epsilon:
        raise Exception("Test failed")
