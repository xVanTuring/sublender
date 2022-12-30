Fix:
* ~~fix undo crash: hard to catch :? cause by texture reload -> better image reload process~~
* ~~fix undo subpanel missing~~
* ~~fix error when toggle visible if~~
* StructRNA of type Material has been removed when dragging slider :hard to catch
Todo:
* add panel to 3d view and options:?
* register blender file uuid -> user preference 
* ~~short class name -> to uid or hash(identifier)~~
* Use nodes group instead ... 
* ~~async for sbsar loading :failed->done~~
* ~~better support for image image~~
* material slider in sublender panel
Workflow:
* ab workflow
* height workflow
* subsurface workflow

Library:
* category/search
* category update operation
* instance/preset
* load preset from package


## Hack
* pip install fake-bpy-module-2.82


## Advanced
* preset
* generate workflow from material
* animation
* preview mode
* output visible if
* add height scale to panel

# CMD
git archive --format zip --output E:\sublender.zip master --prefix sublender/