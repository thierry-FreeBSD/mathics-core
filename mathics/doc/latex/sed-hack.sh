#!/bin/bash
set -x
# Brute force convert Unicode characters in LaTeX that it can't handle
# Workaround for messages of the form:
#    Missing character: There is no ⩵ ("2A75) in font pplr7t!
# Mathics3 MakeBox rules should handle this but they don't.

# Characters that only work in math mode we convert back
# to their ASCII equivalent. Otherwise, since we don't
# understand context, it might not be right to
# use a math-mode designation.
if [[ -f documentation.tex ]] ; then
    cp documentation.tex{,-before-sed}
fi
sed -i -e s/π/\\\\pi/g documentation.tex
sed -i -e s/“/\`\`/g documentation.tex
sed -i -e s/”/''/g documentation.tex
sed -i -e s/”/''/g documentation.tex
sed -i -e s/″/''/g documentation.tex
# sed -i -e s/\\′/'/g documentation.text
#sed -i -e s/′/'/ documentation.tex
sed -i -e s/μ/$\\\\mu$/g documentation.tex
sed -i -e 's/–/--/g' documentation.tex
sed -i -e 's/Φ/$\\\\Phi$/g' documentation.tex
sed -i -e 's/ϕ/Phi/g' documentation.tex
sed -i -e 's/→/->/g' documentation.tex
sed -i -e 's/→/->/g' documentation.tex
sed -i -e 's/⧴/:>/g' documentation.tex
sed -i -e 's/—/-/g' documentation.tex
sed -i -e 's/≤/<=/g' documentation.tex
sed -i -e 's/≠/!=/g' documentation.tex
sed -i -e 's/⩵/==/g' documentation.tex
sed -i -e 's/∧/&&/g' documentation.tex
sed -i -e 's/⧦/\\\\Equiv/g' documentation.tex
sed -i -e 's/⊻/xor/g' documentation.tex
sed -i -e 's/∧/&&/g' documentation.tex
# This may looks he same as the above, but it is different.
sed -i -e 's/∧/&&/g' documentation.tex
sed -i -e 's/‖/||/g' documentation.tex
