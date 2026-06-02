# Kubernetes CRDs: Why `no matches for kind` and How to Fix It

**Author:** katana  
**Date:** June 2, 2026  
**Reading time:** 5 min  
**Tags:** kubernetes, crd, custom-resources, debugging, api-version

---

You define a CustomResourceDefinition (CRD), create a YAML file for your custom resource, run `kubectl apply`, and get hit with:

```
error: resource mapping not found for name: "daily-backup" namespace: "" from "test-backup.yml":
  no matches for kind "Backup" in version "backups.kubedojo.io/v1"
```

If you've ever hit this error, you're not alone. It's one of the most common mistakes when working with CRDs — and the fix is a one-line change.

Let's break down what went wrong.

---

## The CRD Definition

Here's the CRD we're working with:

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: backups.kubedojo.io
spec:
  group: kubedojo.io                    # ← The API group
  scope: Namespaced
  names:
    plural: backups                     # ← Plural resource name
    singular: backup                    # ← Singular resource name
    kind: Backup                        # ← The Kind used in YAML
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              schedule:
                type: string
              target:
                type: string
              retention:
                type: integer
```

Nothing wrong here — this CRD defines a custom resource called `Backup` in the `kubedojo.io` API group.

---

## The (Wrong) YAML

Now look at the resource we tried to create:

```yaml
apiVersion: backups.kubedojo.io/v1    # ← WRONG
kind: Backup
metadata:
  name: daily-backup
spec:
  schedule: "*/5 * * * *"
  target: "/data/postgres"
  retention: 30
```

See `backups.kubedojo.io/v1`? That's the problem.

---

## Why the Error Happens

The `apiVersion` field follows the format:

```
apiVersion: <API-GROUP>/<VERSION>
```

The **API group** is defined in the CRD's `spec.group` field. In our case:

```yaml
spec:
  group: kubedojo.io          # ← This is the group
```

The plural name (`backups`) is part of the resource **metadata**, not the group. It tells Kubernetes how to refer to the resource in URLs (`/apis/kubedojo.io/v1/namespaces/default/backups`), but it is NOT part of the `apiVersion`.

So the correct `apiVersion` is simply:

```yaml
apiVersion: kubedojo.io/v1    # ✅ Just group/version
```

Not:

```yaml
apiVersion: backups.kubedojo.io/v1    # ❌ Plural name has no place here
```

---

## The Full Flow

![CRD API Version Resolution Flow](flow.png)

1. CRD defines `group: kubedojo.io`, `kind: Backup`, `plural: backups`
2. Kubernetes registers the resource at `kubedojo.io/v1`, **not** `backups.kubedojo.io/v1`
3. When you write `apiVersion: backups.kubedojo.io/v1`, Kubernetes looks for a CRD with group `backups.kubedojo.io`
4. No such CRD exists → `no matches for kind "Backup" in version "backups.kubedojo.io/v1"`

---

## The Fix

Change just the `apiVersion` line:

```yaml
apiVersion: kubedojo.io/v1             # ✅ Fixed: just the group/version
kind: Backup
metadata:
  name: daily-backup
spec:
  schedule: "*/5 * * * *"
  target: "/data/postgres"
  retention: 30
```

Then apply again:

```bash
kubectl apply -f test-backup.yml
```

No error — the resource is created successfully.

---

## How to Avoid This Mistake

### 1. Remember the formula

```
apiVersion = spec.group + "/" + version_name
```

The plural name, singular name, and kind are **not** part of the `apiVersion`.

### 2. Check with `kubectl api-resources`

After applying a CRD, list all available resources to see the correct API version:

```bash
kubectl api-resources | grep kubedojo
```

```
NAME       SHORTNAMES   APIVERSION        NAMESPACED   KIND
backups                 kubedojo.io/v1    true         Backup
```

The third column (`APIVERSION`) tells you exactly what to put in your YAML — in this case, `kubedojo.io/v1`.

### 3. Use `kubectl explain`

Once the CRD is installed:

```bash
kubectl explain backup
```

This works and shows the schema — but only after you create a resource correctly. It's a quick sanity check.

---

## What Matters and What Doesn't

| Field | Used in `apiVersion`? | Used for |
|-------|----------------------|----------|
| `spec.group` | ✅ Yes | Determines the API group in `apiVersion` |
| `spec.names.plural` | ❌ No | REST resource URL (`/apis/group/version/.../plural`) |
| `spec.names.singular` | ❌ No | CLI aliases (`kubectl get backup`) |
| `spec.names.kind` | ❌ No | CamelCase Kind in YAML `kind` field |
| `spec.versions[].name` | ✅ Yes | Determines the version in `apiVersion` |

---

## Summary

The `no matches for kind` error with CRDs almost always comes down to one thing: **writing the wrong `apiVersion`**.

- ✅ `apiVersion: kubedojo.io/v1` — correct
- ❌ `apiVersion: backups.kubedojo.io/v1` — wrong (plural name snuck into the group)

The group is what's in `spec.group`. Period. The plural name belongs in URLs and `kubectl` aliases, not in `apiVersion`.

Keep `kubectl api-resources` handy, and you'll never get tripped up by this again.
