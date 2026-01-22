import { describe, it, expect } from 'vitest'
import { enUS } from './en-US'
import { frFR } from './fr-FR'

describe('Internationalization Locales Integrity', () => {
  const getKeys = (obj: Record<string, unknown>, prefix = ''): string[] => {
    return Object.keys(obj).reduce((res: string[], el) => {
      const val = obj[el]
      if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
        return [...res, ...getKeys(val as Record<string, unknown>, prefix + el + '.')]
      }
      return [...res, prefix + el]
    }, [])
  }

  const enKeys = getKeys(enUS)
  const frFRKeys = getKeys(frFR)

  it('fr-FR should have the same keys as en-US', () => {
    const missingInFrFR = enKeys.filter(key => !frFRKeys.includes(key))
    const extraInFrFR = frFRKeys.filter(key => !enKeys.includes(key))

    expect(missingInFrFR, `Missing keys in fr-FR: ${missingInFrFR.join(', ')}`).toEqual([])
    expect(extraInFrFR, `Extra keys in fr-FR: ${extraInFrFR.join(', ')}`).toEqual([])
  })
})
